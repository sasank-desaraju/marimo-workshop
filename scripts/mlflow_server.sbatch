#!/usr/bin/env bash
#SBATCH --job-name=mlflow-ws
#SBATCH --cpus-per-task=2
#SBATCH --mem=4gb
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x-%j.out
##SBATCH --account=TODO          # TODO(HPG): if needed
##SBATCH --qos=TODO
#
# Run an MLflow tracking server on a compute node. Either:
#
#   sbatch scripts/mlflow_server.sbatch   # as its own job (submit from the repo root)
#   bash scripts/mlflow_server.sbatch     # inside a job you already have, e.g. OOD Desktop
#
# While it runs, mlruns/server.env holds its address, which training jobs and
# 03_results.py pick up automatically. To open the UI from your laptop:
#
#   scripts/port_forward.sh <job name> 5000   # then browse to http://localhost:5000
#
# Env: MLFLOW_PORT (default 5000), MLFLOW (launcher, default "uvx mlflow").
#
# Note: MLflow has no login. It listens on the cluster network so jobs on other
# nodes can log to it; treat it as a short-lived workshop server.
set -euo pipefail

# Under sbatch this file runs from a spool copy, so fall back to the submit dir.
here=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if [[ -d $here/notebooks ]]; then
    repo=$here
else
    repo=${SLURM_SUBMIT_DIR:?submit from the repo root}
fi

port=${MLFLOW_PORT:-5000}
host=$(hostname -s)
store=$repo/mlruns
# TODO(HPG): load whatever provides uv or mlflow, e.g. `module load ...`
read -ra mlflow <<< "${MLFLOW:-uvx mlflow}"

if (echo > "/dev/tcp/127.0.0.1/$port") 2> /dev/null; then
    echo "error: port $port is already in use on $host; try MLFLOW_PORT=5001" >&2
    exit 1
fi

mkdir -p "$store"
echo "MLFLOW_TRACKING_URI=http://$host:$port" > "$store/server.env"
trap 'rm -f "$store/server.env"' EXIT INT TERM

cat << MSG
MLflow server at http://$host:$port (job ${SLURM_JOB_ID:-none}, store $store)
From your laptop: scripts/port_forward.sh ${SLURM_JOB_NAME:-<job name>} $port
MSG

# --allowed-hosts: MLflow rejects unknown Host headers, and other nodes will
# address this one by name.
"${mlflow[@]}" server \
    --host 0.0.0.0 \
    --port "$port" \
    --allowed-hosts "$host:$port,localhost:$port,127.0.0.1:$port" \
    --backend-store-uri "sqlite:///$store/mlflow.db" \
    --artifacts-destination "$store/artifacts"
