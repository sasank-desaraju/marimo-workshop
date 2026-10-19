# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "altair",
#     "marimo",
#     "pandas",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")

with app.setup:
    import json
    import os
    from pathlib import Path

    import altair as alt
    import marimo as mo
    import pandas as pd

    RUNS_DIR = Path(os.environ.get("RUNS_DIR", Path(__file__).resolve().parents[1] / "runs"))


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Training runs

    Reads `runs/<timestamp>-<jobid>/` straight off disk: `metrics.csv` (one
    row per epoch), `params.json`, and `model.pt` from `03_train.py`.
    Turn on auto-refresh to watch a Slurm job fill in.
    """)
    return


@app.cell
def _():
    refresh = mo.ui.refresh(options=["2s", "5s", "15s"], label="Auto-refresh")
    refresh
    return (refresh,)


@app.cell
def _(refresh):
    _tick = refresh.value  # a new value on each tick, so this cell re-reads disk
    frames = []
    rows = []
    for metrics_csv in sorted(RUNS_DIR.glob("*/metrics.csv")):
        run = metrics_csv.parent.name
        try:
            frame = pd.read_csv(metrics_csv)
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            continue
        if frame.empty or "epoch" not in frame.columns:
            continue
        frames.append(frame.assign(run=run))
        params_path = metrics_csv.parent / "params.json"
        try:
            params = json.loads(params_path.read_text()) if params_path.is_file() else {}
        except json.JSONDecodeError:
            params = {}
        rows.append({"run": run, **params})

    history = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    params_df = pd.DataFrame(rows)
    mo.stop(
        history.empty,
        mo.callout(
            mo.md(
                f"No epoch rows in `{RUNS_DIR}` yet. "
                "Run `notebooks/03_train.py` or `sbatch scripts/train.sbatch`, "
                "then turn on auto-refresh."
            ),
            kind="warn",
        ),
    )
    _n = int(history["run"].nunique())
    mo.md(f"**{_n}** run{'s' if _n != 1 else ''} in `{RUNS_DIR}`.")
    return history, params_df


@app.cell
def _(history, mo, params_df):
    _last = (
        history.sort_values("epoch")
        .groupby("run", as_index=False)
        .tail(1)
        .rename(columns={"epoch": "epochs_done"})
    )
    summary = params_df.merge(
        _last[["run", "epochs_done", "test_acc", "train_loss"]], on="run", how="left"
    ).sort_values("run", ascending=False)
    for _column in ("test_acc", "train_loss"):
        summary[_column] = summary[_column].astype(float).round(4)
    _show = [
        column
        for column in (
            "run",
            "epochs_done",
            "test_acc",
            "train_loss",
            "epochs",
            "lr",
            "batch_size",
            "normalize",
            "device",
        )
        if column in summary.columns
    ]
    runs_table = mo.ui.table(
        summary[_show],
        selection="multi",
        page_size=6,
        show_column_summaries=False,
        label="Select runs to plot. None selected plots all.",
    )
    runs_table
    return (runs_table,)


@app.cell
def _(mo):
    metric = mo.ui.dropdown(
        {"Test accuracy": "test_acc", "Train loss": "train_loss", "Test loss": "test_loss"},
        value="Test accuracy",
        label="Metric",
    )
    metric
    return (metric,)


@app.cell
def _(history, metric, mo, runs_table):
    _selected = runs_table.value
    if isinstance(_selected, pd.DataFrame) and not _selected.empty:
        _plotted = history[history["run"].isin(_selected["run"])]
    else:
        _plotted = history
    _chart = (
        alt.Chart(_plotted)
        .mark_line(point=True)
        .encode(
            x=alt.X("epoch:Q", title="Epoch"),
            y=alt.Y(f"{metric.value}:Q", title=metric.selected_key),
            color=alt.Color("run:N", title="Run"),
            tooltip=["run", "epoch", alt.Tooltip(f"{metric.value}:Q", format=".3f")],
        )
        .properties(height=300, width=680)
    )
    mo.ui.altair_chart(_chart)
    return


if __name__ == "__main__":
    app.run()
