#!/usr/bin/env bash
# Forward ports from your laptop to the compute node running one of your HPG jobs.
#
# Usage: scripts/port_forward.sh JOB_NAME PORT [PORT ...]
#
#   JOB_NAME  the --job-name of a running job (yours), e.g. marimo-ws
#   PORT      2718 (same port on both ends) or LOCAL:REMOTE, e.g. 8080:2718
#
# Examples:
#   scripts/port_forward.sh marimo-ws 2718
#   scripts/port_forward.sh marimo-ws 8080:2718
#
# Env:
#   HPG_HOST  ssh host or ~/.ssh/config alias for the HPG login node (default: hpg)
#   PF_MODE   jump  (default) ssh through the login node to the compute node;
#                   works with servers bound to localhost (marimo's default)
#             login forward via the login node only; needs servers bound to 0.0.0.0
#
# Runs in the foreground; Ctrl-C closes the tunnel.
set -euo pipefail

usage() {
    sed -n '2,/^set -euo/{/^set/d;s/^# \{0,1\}//;p}' "$0" >&2
    exit "${1:-1}"
}
die() {
    echo "error: $*" >&2
    exit 1
}

[[ ${1:-} == -h || ${1:-} == --help ]] && usage 0
[[ $# -ge 2 ]] || usage

job=$1
shift
hpg=${HPG_HOST:-hpg}
mode=${PF_MODE:-jump}
[[ $job =~ ^[A-Za-z0-9._-]+$ ]] || die "job name '$job' has unexpected characters"
[[ $mode == jump || $mode == login ]] || die "PF_MODE must be 'jump' or 'login'"

# Parse ports up front so a typo fails before we touch the network.
pairs=()
for spec in "$@"; do
    [[ $spec =~ ^([0-9]+)(:([0-9]+))?$ ]] || die "bad port '$spec' (use 2718 or 8080:2718)"
    pairs+=("${BASH_REMATCH[1]}:${BASH_REMATCH[3]:-${BASH_REMATCH[1]}}")
done

# One line per matching running job: "<user> <jobid> <nodelist>".
echo "Looking up your running job '$job' on $hpg ..."
# shellcheck disable=SC2029  # $job is validated above and meant to expand here
jobs=$(ssh "$hpg" "squeue -u \"\$USER\" -n '$job' -h -t RUNNING -o '%u %i %N'") ||
    die "could not run squeue on $hpg (is 'ssh $hpg' set up?)"
[[ -n $jobs ]] || die "no running job named '$job'. Check with: ssh $hpg squeue --me"
if (($(wc -l <<< "$jobs") > 1)); then
    echo "warning: several running jobs named '$job'; using the first:" >&2
    echo "$jobs" >&2
fi
read -r user jobid nodelist <<< "$(head -n1 <<< "$jobs")"

# Multi-node jobs report e.g. c0101a-s[1-2]; forward to the first node.
node=$nodelist
if [[ $node == *"["* ]]; then
    # shellcheck disable=SC2029
    node=$(ssh "$hpg" "scontrol show hostnames '$nodelist' | head -n1")
fi

forwards=()
echo "Job $jobid is on $node. Open:"
for pair in "${pairs[@]}"; do
    local_port=${pair%%:*}
    remote_port=${pair##*:}
    if [[ $mode == jump ]]; then
        forwards+=(-L "$local_port:localhost:$remote_port")
    else
        forwards+=(-L "$local_port:$node:$remote_port")
    fi
    echo "  http://localhost:$local_port  ->  $node:$remote_port"
done
echo "Ctrl-C to stop."

# TODO(HPG): confirm users may ssh to nodes running their jobs (needed for jump mode).
if [[ $mode == jump ]]; then
    exec ssh -N -J "$hpg" "${forwards[@]}" "$user@$node"
else
    exec ssh -N "${forwards[@]}" "$hpg"
fi
