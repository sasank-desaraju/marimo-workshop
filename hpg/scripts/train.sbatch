#!/usr/bin/env bash
#SBATCH --job-name=mnist1d-train

# Set the below account to your group. List yours with: showAssoc $USER
#SBATCH --account=dr.allie.gator

#SBATCH --cpus-per-task=4
#SBATCH --mem=8gb
#SBATCH --time=00:15:00
#SBATCH --output=logs/%x-%j.out
# MNIST-1D trains fine on CPU. To use an L4 GPU from HPG, delete one # from the below line to uncomment it.
##SBATCH --gpus=1
#
# Train using notebooks/n3_train.py. Submit from the hpg/ folder after preprocessing the data with
# notebooks/n1_preprocess.py.

# Extra arguments go to the training script:
#   sbatch scripts/train.sbatch --epochs 5 --lr 0.01

set -euo pipefail

module load uv  # (just an alias for module load conda)
echo "Job $SLURM_JOB_ID on $(hostname -s)"
nvidia-smi -L 2>/dev/null || true
uv run notebooks/n3_train.py "$@"
