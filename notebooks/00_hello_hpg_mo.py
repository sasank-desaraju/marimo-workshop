# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "matplotlib",
#     "numpy",
# ]
# ///

# Only this file uses the *_mo.py suffix, so JupyterLab opens it in marimo on double-click.

import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import os
    import platform
    import socket
    import sys

    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np

    return mo, np, os, platform, plt, socket, sys


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Hello, HiPerGator 👋

    A marimo notebook is a plain Python file where cells form a **dataflow
    graph**: when you change something, every cell that depends on it re-runs,
    and nothing else does. There is no hidden state and no "run all" to forget.

    Drag the sliders below and watch the plot follow.
    """)
    return


@app.cell
def _(mo):
    frequency = mo.ui.slider(0.5, 5.0, step=0.5, value=1.5, label="Frequency", show_value=True)
    damping = mo.ui.slider(0.0, 1.0, step=0.05, value=0.2, label="Damping", show_value=True)
    mo.hstack([frequency, damping], justify="start", gap=2)
    return damping, frequency


@app.cell
def _(damping, frequency, np, plt):
    # This cell reads `frequency.value` and `damping.value`, so marimo re-runs it
    # whenever either slider moves.
    t = np.linspace(0, 10, 500)
    wave = np.exp(-damping.value * t) * np.sin(2 * np.pi * frequency.value * t)

    _fig, _ax = plt.subplots(figsize=(8, 2.5))
    _ax.plot(t, wave, lw=1.5)
    _ax.set_xlabel("time")
    _ax.set_ylim(-1.05, 1.05)
    _ax.set_title(f"A damped wave at {frequency.value} Hz")
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Where am I running?

    On HiPerGator this notebook runs inside a Slurm job on a compute node, not
    on your laptop. The numbers below come from that node.
    """)
    return


@app.cell
def _(os):
    def allocated_cpus() -> int:
        """CPUs this process may use. Slurm limits this, os.cpu_count() does not."""
        try:
            return len(os.sched_getaffinity(0))
        except AttributeError:  # macOS / Windows have no affinity API
            return os.cpu_count() or 1

    return (allocated_cpus,)


@app.cell
def _(allocated_cpus, mo, os, platform, socket, sys):
    _slurm = {k: v for k, v in sorted(os.environ.items()) if k.startswith("SLURM_")}
    _keep = (
        "SLURM_JOB_ID",
        "SLURM_JOB_NAME",
        "SLURM_JOB_PARTITION",
        "SLURM_CPUS_ON_NODE",
        "SLURM_MEM_PER_NODE",
        "SLURM_JOB_END_TIME",
    )
    _host = mo.md(
        f"""
        | | |
        |---|---|
        | Host | `{socket.gethostname()}` |
        | User | `{os.environ.get("USER", "?")}` |
        | Working directory | `{os.getcwd()}` |
        | Python | `{sys.version.split()[0]}` on `{platform.platform()}` |
        | CPUs allocated / on node | **{allocated_cpus()}** / {os.cpu_count()} |
        | GPUs visible | `{os.environ.get("CUDA_VISIBLE_DEVICES", "none")}` |
        """
    )
    _jobs = (
        mo.ui.table(
            [{"variable": k, "value": _slurm[k]} for k in _keep if k in _slurm],
            selection=None,
            label=f"Slurm job (showing {sum(k in _slurm for k in _keep)} of {len(_slurm)} SLURM_* variables)",
        )
        if _slurm
        else mo.callout(
            mo.md("No `SLURM_*` variables: this is not running inside a Slurm job."), kind="warn"
        )
    )
    mo.hstack([_host, _jobs], widths="equal", gap=2, align="start")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Try this:** this file is `notebooks/00_hello_hpg_mo.py`. The `_mo.py`
    suffix is what the JupyterLab marimo extension uses to open a file in
    marimo on double-click. The pipeline notebooks are plain `.py`.
    """)
    return


if __name__ == "__main__":
    app.run()
