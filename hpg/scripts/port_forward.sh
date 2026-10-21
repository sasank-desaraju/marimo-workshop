#!/usr/bin/env bash

# Reach a port on the HPG node running your job at http://localhost:PORT.
# Edit these three lines, then run: bash scripts/port_forward.sh
GATORLINK=albert.gator@hpg.rc.ufl.edu
JOB=marimo-ws
PORT=2718

set -euo pipefail
host=$GATORLINK
sock=/tmp/hpg-pf-$GATORLINK

ssh -fNM -S "$sock" "$host"  # log in once (password + Duo); the steps below reuse it
trap 'ssh -S "$sock" -O exit "$host" 2>/dev/null' EXIT

node=$(ssh -S "$sock" "$host" "squeue -u $GATORLINK -n $JOB -h -t R -o %N" | head -n1)
[[ -n $node ]] || { echo "No running job named $JOB"; exit 1; }

ssh -S "$sock" -O forward -L "$PORT:$node:$PORT" "$host"
read -rp "Open http://localhost:$PORT (node $node). Press Enter to close. "
