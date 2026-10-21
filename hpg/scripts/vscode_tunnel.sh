#!/usr/bin/env bash
# Start a VS Code tunnel from inside an HPG job, so VS Code on your laptop
# (Remote - Tunnels extension) or https://vscode.dev can attach to this node.
#
# Usage: bash scripts/vscode_tunnel.sh [TUNNEL_NAME]
#
# Run it from a terminal inside a job (e.g. the OOD Desktop), not a login node.
# The first time, it prints a device-login URL and code for GitHub/Microsoft.
# The tunnel lives as long as this process (and the job); Ctrl-C stops it.
set -euo pipefail

if [[ -z ${SLURM_JOB_ID:-} ]]; then
    echo "warning: not inside a Slurm job. Please run this on a compute node." >&2
fi

if ! command -v code > /dev/null && type module &> /dev/null; then
    module load vscode 2> /dev/null || true # TODO(HPG): confirm the module name
fi
if ! command -v code > /dev/null; then
    cat >&2 << 'MSG'
error: no `code` command found. Install the standalone VS Code CLI once:

  mkdir -p ~/.local/bin && curl -L 'https://code.visualstudio.com/sha/download?build=stable&os=cli-alpine-x64' | tar -xz -C ~/.local/bin

then re-run this script.
MSG
    exit 1
fi

# Tunnel names are limited to 20 characters.
name=${1:-hpg-${SLURM_JOB_ID:-$(hostname -s)}}
name=${name:0:20}
echo "Starting VS Code tunnel '$name' on $(hostname -s) ..."
exec code tunnel --accept-server-license-terms --name "$name"
