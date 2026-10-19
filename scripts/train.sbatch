#!/usr/bin/env bash
#SBATCH --job-name=mnist1d-train
#SBATCH --cpus-per-task=4
#SBATCH --mem=8gb
#SBATCH --time=00:15:00
#SBATCH --output=logs/%x-%j.out
# TODO(HPG): account/QOS, if your group needs them set explicitly.
##SBATCH --account=TODO
##SBATCH --qos=TODO
# MNIST-1D trains fine on CPU. For an L4, uncomment the next line.
# No partition directive: https://docs.rc.ufl.edu/scheduler/gpu_access/
##SBATCH --gpus=1
#
# Train notebooks/03_train.py as a batch job. Submit from the repo root, after
# notebooks/01_preprocess.py has written data/processed/mnist1d.npz.
# Extra arguments go straight to the training script:
#
#   sbatch scripts/train.sbatch --epochs 5 --lr 0.01
#
# Each run writes runs/<timestamp>-<jobid>/{params.json,metrics.csv,model.pt}.
# Override the Python launcher with RUN, e.g. RUN=python if an env is active.
set -euo pipefail

cd "${SLURM_SUBMIT_DIR:-.}"
if [[ ! -f notebooks/03_train.py ]]; then
    echo "error: submit from the repo root (no notebooks/03_train.py in $PWD)" >&2
    exit 1
fi

# uv comes with the conda module. https://docs.rc.ufl.edu/software/uv/
module load conda
read -ra run <<< "${RUN:-uv run}"

echo "Job ${SLURM_JOB_ID:-none} (${SLURM_JOB_NAME:-local}) on $(hostname -s) at $(date '+%F %T')"
if command -v nvidia-smi > /dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
fi

# `uv run` stops parsing at `--` and forwards the rest. A plain python
# launcher (RUN=python) must see the flags itself, so don't insert `--`.
case $(basename "${run[0]}") in
    uv | uvx) "${run[@]}" notebooks/03_train.py -- "$@" ;;
    *) "${run[@]}" notebooks/03_train.py "$@" ;;
esac
