# Marimo on HiPerGator for scientific work

Materials for the live Zoom workshop **Marimo on HiPerGator (HPG) for
scientific work**, Thu Oct 22 2026, 10:40 to noon ET, run with UF Research
Computing. This repo covers the HPG segment (about 20 minutes, Sasank).
Marimo 101, local use, and SQL are covered separately by Piyush.

> **Draft.** Lines marked `TODO(HPG)` need HPG-specific facts confirmed before
> the workshop.

Everything uses **MNIST-1D**: a small dataset generated locally in about a
second, so there is nothing to download, and it trains in seconds on a CPU.
Training uses a GPU when the job has one. The data stays MNIST-1D either way.

Only `notebooks/00_hello_hpg_mo.py` uses the `_mo.py` suffix. The JupyterLab
marimo extension opens those files in marimo on double-click once JupyterLab
is new enough (see the Jupyter route). The pipeline notebooks are plain `.py`
(open them with `uvx marimo edit` or the launcher's "Edit with marimo").

## Agenda (HPG segment, ~20 minutes)

| Time | Topic |
|---|---|
| 0:00 | Routes: OOD Marimo, Jupyter Notebook, Desktop + tunnel |
| 0:04 | Preprocess: `01_preprocess.py` in the editor, then the same file from the CLI |
| 0:09 | Dataset: `02_dataset.py` visuals, then pytest (break the length assert live) |
| 0:14 | `sbatch scripts/train.sbatch --epochs 5` and glance at the log |
| 0:17 | `04_results.py`: pick the run, turn on auto-refresh |
| 0:20 | Take-home and Q&A |

## Setup (once)

```bash
# On HPG. TODO(HPG): recommended location (e.g. /blue/<group>/$USER vs home).
cd /blue/TODO_GROUP/$USER
git clone TODO_REPO_URL marimo-workshop
cd marimo-workshop
cp .env.example .env              # then paste your NaviGator key into .env

# uv comes with the conda module. https://docs.rc.ufl.edu/software/uv/
module load conda
# PyTorch is several GB. RC suggests symlinking ~/.cache onto /blue:
#   ln -s /blue/TODO_GROUP/$USER/.cache ~/.cache
# UV_CACHE_DIR is the other way to keep that cache off the home quota.
export UV_CACHE_DIR=/blue/TODO_GROUP/$USER/.cache/uv
# TODO(HPG): PyPI torch wheels need a recent NVIDIA driver. Check that
# torch.cuda.is_available() is True on an L4 node (if not, training uses CPU,
# which is fine for MNIST-1D).
```

Each notebook declares its own dependencies in a PEP 723 header, so
`uvx marimo edit --sandbox <file>` or `uv run <file>` builds the right
environment on first use and reuses it after that. `03_train.py` is a plain
script with the same kind of header. HPG also has
`module load marimo/0.25.2`, the same version as these notebooks.
The commands below still go through uv.

## Routes

### 1. OOD Marimo app (just to show)

1. Open OnDemand, start the **TODO(HPG): Marimo app name** app with the working
   directory set to this repo (or a single file). On a compute node,
   `module load marimo/0.25.2` is the cluster install.
2. Open `notebooks/00_hello_hpg_mo.py`: move the sliders, then look at the host
   and Slurm job info.
3. Open the AI chat side panel. It talks to NaviGator through the
   `[tool.marimo.ai]` settings in `pyproject.toml`, with the key read from
   `.env`.
   TODO(HPG): confirm the OOD app's marimo version understands `env:` keys and
   has `openai` installed; otherwise set the key in Settings → AI.

### 2. OOD Jupyter Notebook (just to show)

1. Interactive Apps → Servers → **Jupyter Notebook**, then open this repo in
   the file browser. https://docs.rc.ufl.edu/interfaces/jupyter_ood/
2. Double-click `notebooks/00_hello_hpg_mo.py`. That `_mo.py` suffix is what
   marimo-jupyter-extension 0.5.0 uses to open a file in marimo, and the
   extension needs JupyterLab >= 4.5. HPG is on JupyterLab 3.6.6; an upgrade
   is requested from RC, so the double-click does not open marimo yet. Other
   `.py` files open in the normal editor.

### 3. OOD Desktop (main demo)

Start the **TODO(HPG): Desktop app** on an L4: partition `hpg-turin`, gres
`gpu:1`. The `hwgui` partition also has L4s if the desktop needs hardware
acceleration (https://docs.rc.ufl.edu/scheduler/gpu_access/). Put
`--job-name=marimo-ws` in **Additional SLURM Options** (long-form flags only).
Open a terminal in the desktop, then, from the repo root:

```bash
cd /blue/TODO_GROUP/$USER/marimo-workshop

# a) VS Code tunnel (its own terminal tab; first run asks you to log in)
bash scripts/vscode_tunnel.sh

# b) Preprocess, interactively
uvx marimo edit --sandbox notebooks/01_preprocess.py

# c) The same notebook as a script. Flags after `--` are the widget values.
uv run notebooks/01_preprocess.py -- --out data/processed --normalize zscore --filter smooth

# d) Dataset: plots, then the tests (break test_sequence_length live)
uvx marimo edit --sandbox notebooks/02_dataset.py
uv run pytest notebooks/02_dataset.py

# e) Short training job. Reads data/processed/mnist1d.npz.
sbatch scripts/train.sbatch --epochs 5
squeue --me
tail -f logs/mnist1d-train-*.out

# f) Watch the run folder fill in (turn on auto-refresh)
uvx marimo edit --sandbox --headless --port 2718 notebooks/04_results.py
```

On a laptop, without Slurm, steps (c), (d), and training are:

```bash
uv run notebooks/01_preprocess.py -- --out data/processed --normalize zscore --filter smooth
uv run pytest notebooks/02_dataset.py
uv run notebooks/03_train.py --epochs 2
uvx marimo edit --sandbox notebooks/04_results.py
```

`03_train.py` cannot say `import 02_dataset` because the filename starts with
a digit. It loads that notebook by path; `MNIST1D` is a normal class once the
file is loaded.

On your laptop, forward the headless marimo from the desktop job:

```bash
scripts/port_forward.sh marimo-ws 2718
# http://localhost:2718  (add the ?access_token=... marimo printed)
```

`port_forward.sh` expects an ssh alias `hpg` (override with `HPG_HOST`).
The login host and this ControlMaster block match RC's example
(https://docs.rc.ufl.edu/interfaces/terminal/):

```sshconfig
Host hpg
    HostName hpg.rc.ufl.edu
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
  00_hello_hpg_mo.py        reactivity tour + where-am-I; the only *_mo.py file
  01_preprocess.py          generate, transform, save data/processed/
  02_dataset.py             MNIST1D Dataset, plots, pytest
  03_train.py               plain training script (not a marimo notebook)
  04_results.py             plot runs/<id>/ from disk, with auto-refresh
  mnist1d_cpu_fallback.py   standalone backup demo
scripts/
  train.sbatch              Slurm job that runs 03_train.py
  port_forward.sh           laptop → node tunnel, found by job name
  vscode_tunnel.sh          `code tunnel` from inside a job
logs/                       Slurm output (git-ignored)
data/processed/             npz + metadata.json from 01_preprocess.py (git-ignored)
runs/                       one folder per training run (git-ignored)
pyproject.toml              marimo project settings (NaviGator AI provider)
.env.example                template for .env (API key)
```

`uvx marimo check --ignore-scripts notebooks` skips `03_train.py`. Without
`--ignore-scripts`, check stops on that script.

## Where runs go

`01_preprocess.py` writes `data/processed/mnist1d.npz` and
`data/processed/metadata.json`. Training reads that file and writes
`runs/<timestamp>-<job id>/` with `params.json`, `metrics.csv` (flushed each
epoch), and `model.pt`. `04_results.py` reads those files directly. Set
`RUNS_DIR` if the run folder should live somewhere else.

## License and citation

Code is MIT licensed (see `LICENSE`). To cite these materials, see
`CITATION.cff`.
