#!/usr/bin/env bash
#SBATCH --job-name=mnist1d-train
#SBATCH --cpus-per-task=4
#SBATCH --mem=8gb
#SBATCH --time=00:15:00
#SBATCH --output=logs/%x-%j.out
# MNIST-1D trains fine on CPU. For an L4, delete one # from the next line.
##SBATCH --gpus=1
#
# Train notebooks/03_train.py. Submit from the hpg/ folder after running
# notebooks/01_preprocess.py. Extra arguments go to the training script:
#   sbatch scripts/train.sbatch --epochs 5 --lr 0.01
set -euo pipefail

module load conda  # provides uv
echo "Job $SLURM_JOB_ID on $(hostname -s)"
nvidia-smi -L 2>/dev/null || true
uv run notebooks/03_train.py "$@"
