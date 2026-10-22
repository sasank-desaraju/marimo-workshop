#!/usr/bin/env bash
# Start a VS Code tunnel from inside an HPG job, so VS Code on your laptop
# (Remote - Tunnels extension) or https://vscode.dev can attach to this node.
#
# Usage: bash scripts/vscode_tunnel.sh [TUNNEL_NAME]
#
# Run it from a terminal inside a job (e.g. the OOD Desktop), not a login node.
# UF Docs page: https://docs.rc.ufl.edu/domain/vscode_development/


ml vscode # ml is shorthand for module load

code tunnel
