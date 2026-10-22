#!/usr/bin/env bash

# Reach a port on the HPG node running your job at http://localhost:PORT.
# Edit these three lines, then run: bash scripts/port_forward.sh
GATORLINK=albert.gator
JOB=marimo-ws
PORT=2718

set -euo pipefail
host=$GATORLINK@hpg.rc.ufl.edu
sock=/tmp/hpg-pf-$GATORLINK

ssh -fNM -S "$sock" "$host"  # log in once (password + Duo); the steps below reuse it
trap 'ssh -S "$sock" -O exit "$host" 2>/dev/null' EXIT

node=$(ssh -S "$sock" "$host" "squeue -u $GATORLINK -n $JOB -h -t R -o %N" | head -n1)
[[ -n $node ]] || { echo "No running job named $JOB"; exit 1; }

# marimo listens only on the node's own localhost, so hop through the login
# session to the node and forward to localhost there. Needs an SSH key in
# ~/.ssh/authorized_keys on HPG (see the README).
echo "Open http://localhost:$PORT (node $node). Ctrl-C to close."
ssh -N -o ProxyCommand="ssh -S $sock -W %h:%p $host" \
  -o StrictHostKeyChecking=accept-new \
  -L "$PORT:localhost:$PORT" "$GATORLINK@$node"
