# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "altair",
#     "marimo",
#     "numpy",
#     "pandas",
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

    import altair as alt
    import marimo as mo
    import numpy as np
    import pandas as pd

    return alt, mo, np, os, pd, platform, socket, sys


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Hello, HiPerGator! 🐊

    A marimo notebook is a plain Python file where every cell knows what other cells it's dependent on.
    This lets each cell re-run whenever it needs to.
    There's not "hidden state" where you can lose track of what variable has what value.
    It's also great for interactivity and visualization!

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
def _(alt, damping, frequency, np, pd):
    # This cell reads from `frequency` and `damping` which are in the cell above, so marimo re-runs it
    # whenever either slider moves.
    t = np.linspace(0, 10, 500)
    wave = np.exp(-damping.value * t) * np.sin(2 * np.pi * frequency.value * t)

    (
        alt.Chart(pd.DataFrame({"time": t, "wave": wave}))
        .mark_line()
        .encode(x="time:Q", y=alt.Y("wave:Q", title=None, scale=alt.Scale(domain=[-1, 1])))
        .properties(width=640, height=180, title=f"A damped wave at {frequency.value} Hz")
    )
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
    _gpus = [g for g in os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",") if g]
    _host = mo.md(
        f"""
        | | |
        |---|---|
        | Host | `{socket.gethostname()}` |
        | User | `{os.environ.get("USER", "?")}` |
        | Working directory | `{os.getcwd()}` |
        | Python | `{sys.version.split()[0]}` on `{platform.platform()}` |
        | CPUs allocated / on node | **{allocated_cpus()}** / {os.cpu_count()} |
        | GPUs allocated | **{len(_gpus)}** (`CUDA_VISIBLE_DEVICES={",".join(_gpus) or "unset"}`) |
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
    mo.hstack(
        [
            mo.md("Made by **Sasank Desaraju**."),
            mo.image(src=mo.notebook_dir().parent / "assets" / "linktree_qr.png", width=120),
        ],
        justify="start",
        align="center",
        gap=1,
    )
    return


if __name__ == "__main__":
    app.run()
