#!/usr/bin/env bash
#SBATCH --job-name=mnist1d-train
#SBATCH --cpus-per-task=4
#SBATCH --mem=8gb
#SBATCH --time=00:15:00
#SBATCH --output=logs/%x-%j.out
# TODO(HPG): account/QOS, if your group needs them set explicitly.
##SBATCH --account=TODO
##SBATCH --qos=TODO
# MNIST-1D trains fine on CPU. To run on an L4 anyway, uncomment and fill in:
##SBATCH --partition=TODO        # TODO(HPG): GPU partition name
##SBATCH --gpus=TODO:1           # TODO(HPG): L4 GPU type string
#
# Train notebooks/02_train.py as a batch job. Submit from the repo root; any
# extra arguments go straight to the training script:
#
#   sbatch scripts/train.sbatch --epochs 30 --lr 0.003
#
# Metrics land in runs/<run name>/, and in MLflow too if a server from
# scripts/mlflow_server.sbatch is running (found via mlruns/server.env).
# Override the Python launcher with RUN, e.g. RUN=python if an env is active.
set -euo pipefail

cd "${SLURM_SUBMIT_DIR:-.}"
if [[ ! -f notebooks/02_train.py ]]; then
    echo "error: submit from the repo root (no notebooks/02_train.py in $PWD)" >&2
    exit 1
fi

# TODO(HPG): load whatever provides uv (or python with torch), e.g. `module load ...`
read -ra run <<< "${RUN:-uv run}"

echo "Job ${SLURM_JOB_ID:-none} (${SLURM_JOB_NAME:-local}) on $(hostname -s) at $(date '+%F %T')"
if command -v nvidia-smi > /dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
fi

"${run[@]}" notebooks/02_train.py -- "$@"
