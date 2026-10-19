# Marimo on HiPerGator for scientific work

Materials for the live Zoom workshop **Marimo on HiPerGator (HPG) for
scientific work**, Thu Oct 22 2026, 10:40 to noon ET, run with UF Research
Computing. This repo covers the HPG part (Sasank). Marimo 101, local use, and
SQL are covered separately by Piyush.

> **Draft.** Lines marked `TODO(HPG)` need HPG-specific facts confirmed before
> the workshop.

Everything uses **MNIST-1D**: a small dataset generated locally in about a
second, so there is nothing to download, and it trains in seconds on a CPU.
The code picks a GPU automatically when one is there, but the data stays the
same.

## Agenda (HPG segment)

| Time | Topic |
|---|---|
| 0:00 | Why marimo on HPG: plain `.py` notebooks, reactive, run as scripts and batch jobs |
| 0:03 | OOD **Marimo** app: open the repo, `00_hello_hpg.py`, NaviGator AI in the side panel |
| 0:08 | OOD **JupyterLab** with the marimo plugin |
| 0:10 | OOD **Desktop** on an L4 GPU, launched with a job name |
| 0:13 | Main demo: VS Code tunnel, Dataset notebook, same file from the CLI, `sbatch`, MLflow + port forwarding, results notebook |
| 0:27 | Take-home and Q&A |

## Setup (once)

```bash
# On HPG. TODO(HPG): recommended location (e.g. /blue/<group>/$USER vs home).
cd /blue/TODO_GROUP/$USER
git clone TODO_REPO_URL marimo-workshop
cd marimo-workshop
cp .env.example .env              # then paste your NaviGator key into .env

# TODO(HPG): how to get uv (module name, or the standalone installer).
module load TODO_UV_MODULE
# Keep uv's package cache (PyTorch is several GB) off your home quota.
export UV_CACHE_DIR=/blue/TODO_GROUP/$USER/.cache/uv
# TODO(HPG): PyPI torch wheels need a recent NVIDIA driver. Check that
# torch.cuda.is_available() is True on an L4 node (if not, the code quietly
# falls back to CPU, which is fine for MNIST-1D).
```

Each notebook declares its own dependencies in a PEP 723 header, so
`uvx marimo edit --sandbox <file>` or `uv run <file>` builds the right
environment on first use and reuses it after that.

## Routes

### 1. OOD Marimo app (just to show)

1. Open OnDemand, start the **TODO(HPG): Marimo app name** app with the working
   directory set to this repo (or a single file).
2. Open `notebooks/00_hello_hpg.py`: move the sliders, then look at the host
   and Slurm job info.
3. Open the AI chat side panel. It talks to NaviGator through the
   `[tool.marimo.ai]` settings in `pyproject.toml`, with the key read from
   `.env`.
   TODO(HPG): confirm the OOD app's marimo version understands `env:` keys and
   has `openai` installed; otherwise set the key in Settings → AI.

### 2. OOD JupyterLab with the marimo plugin (just to show)

1. Start **TODO(HPG): JupyterLab app** and `cd` to this repo in the file browser.
2. Launch marimo from the **TODO(HPG): plugin's launcher tile / menu**, then open
   `notebooks/00_hello_hpg.py`.

### 3. OOD Desktop on an L4 (main demo)

Start the **TODO(HPG): Desktop app** with an L4 GPU and job name `marimo-ws`
(TODO(HPG): which form field takes `--job-name=marimo-ws`, and the L4
partition/GPU string). Open a terminal in the desktop, then:

```bash
cd /blue/TODO_GROUP/$USER/marimo-workshop

# a) VS Code tunnel (in its own terminal tab; first run asks you to log in),
#    then attach from VS Code on your laptop or from vscode.dev
bash scripts/vscode_tunnel.sh

# b) Build and inspect the Dataset interactively
uvx marimo edit --sandbox notebooks/01_dataset_explore.py

# c) The same training notebook, now as a plain script
uv run notebooks/02_train.py -- --epochs 5 --lr 0.01

# d) MLflow server inside this job (or `sbatch scripts/mlflow_server.sbatch`)
bash scripts/mlflow_server.sbatch &

# e) Submit a short training job; it finds MLflow via mlruns/server.env
sbatch scripts/train.sbatch --epochs 30
squeue --me
tail -f logs/mnist1d-train-*.out

# f) Watch results come in (turn on auto-refresh)
uvx marimo edit --sandbox --headless --port 2718 notebooks/03_results.py
```

On your laptop (from a local clone, or just a copy of this one script),
connect to marimo and MLflow by job name:

```bash
scripts/port_forward.sh marimo-ws 2718 5000
# marimo: http://localhost:2718 (add the ?access_token=... marimo printed)
# MLflow: http://localhost:5000
```

`port_forward.sh` expects an ssh alias `hpg` (override with `HPG_HOST`):

```sshconfig
Host hpg
    HostName hpg.rc.ufl.edu        # TODO(HPG): confirm login host
    User your_gatorlink
    ControlMaster auto             # one login (and one MFA prompt) per session
    ControlPath ~/.ssh/cm-%r@%h-%p
    ControlPersist 10m
```

### No cluster? Fallback

`notebooks/mnist1d_cpu_fallback.py` is one self-contained file that runs on
any laptop:

```bash
uvx marimo edit --sandbox notebooks/mnist1d_cpu_fallback.py
```

## Repo layout

```
notebooks/
  00_hello_hpg.py           reactivity tour + where-am-I (host, CPUs, Slurm vars)
  01_dataset_explore.py     build and inspect the MNIST-1D Dataset
  02_train.py               train a 1D CNN; notebook, CLI script, or batch job
  03_results.py             compare runs from MLflow or CSV, with auto-refresh
  mnist1d_cpu_fallback.py   standalone backup demo
src/
  mnist1d_data.py           MNIST1D Dataset + DataLoaders (shared)
  tracking.py               run logging (CSV, optional MLflow) and loading
scripts/
  train.sbatch              Slurm job that runs 02_train.py
  mlflow_server.sbatch      MLflow server on a compute node (sbatch or bash)
  port_forward.sh           laptop → node tunnels, found by job name
  vscode_tunnel.sh          `code tunnel` from inside a job
logs/                       Slurm output (git-ignored)
runs/, mlruns/              created by training / MLflow (git-ignored)
pyproject.toml              marimo project settings (NaviGator AI provider)
.env.example                template for .env (API key, optional MLflow URI)
```

## Where runs go

Every training run writes `runs/<timestamp>-<job id>/` with `params.json`,
`metrics.csv` (updated each epoch), and `model.pt`. If an MLflow server is
configured (`MLFLOW_TRACKING_URI`, or `mlruns/server.env` while
`mlflow_server.sbatch` runs), the same params and metrics go to MLflow too.
If the server is unreachable, training carries on with CSV only.

## License and citation

Code is MIT licensed (see `LICENSE`). To cite these materials, see
`CITATION.cff`.
