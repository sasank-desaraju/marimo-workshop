# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "altair",
#     "marimo",
#     "mlflow-skinny",
#     "pandas",
# ]
# ///

import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys

    import altair as alt
    import marimo as mo

    # Shared code lives in ../src, so every notebook uses the same Dataset and logger.
    _src = str(mo.notebook_dir().parent / "src")
    if _src not in sys.path:
        sys.path.insert(0, _src)
    from tracking import RUNS_DIR, load_csv_runs, load_mlflow_runs, tracking_uri

    return RUNS_DIR, alt, load_csv_runs, load_mlflow_runs, mo, tracking_uri


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Compare training runs

    Reads every run that `02_train.py` logged, from MLflow if a server is
    configured or from the CSV files in `runs/` otherwise. Turn on auto-refresh
    to watch a batch job fill in while it trains.
    """)
    return


@app.cell
def _(mo, tracking_uri):
    uri = tracking_uri()
    source = mo.ui.dropdown(
        ["MLflow", "CSV"] if uri else ["CSV"],
        value="MLflow" if uri else "CSV",
        label="Source",
    )
    refresh = mo.ui.refresh(options=["5s", "15s", "1m"], label="Auto-refresh")
    mo.hstack([source, refresh], justify="start", gap=2)
    return refresh, source, uri


@app.cell
def _(RUNS_DIR, load_csv_runs, load_mlflow_runs, mo, refresh, source, uri):
    refresh  # re-run this cell on every refresh tick
    if source.value == "MLflow":
        history, params = load_mlflow_runs(uri)
        _where = f"MLflow at `{uri}`"
    else:
        history, params = load_csv_runs()
        _where = f"`{RUNS_DIR}`"
    mo.stop(
        history.empty,
        mo.callout(mo.md(f"No runs in {_where} yet. Train one with `02_train.py`."), kind="warn"),
    )
    _n = history["run"].nunique()
    mo.md(f"**{_n}** run{'s' * (_n != 1)} from {_where}.")
    return history, params


@app.cell
def _(history, mo, params):
    # One row per run: its settings plus how it ended up.
    _last = history.sort_values("epoch").groupby("run").last()
    summary = (
        params.set_index("run")
        .join(_last[["epoch", "test_acc", "train_loss"]].rename(columns={"epoch": "epochs_done"}))
        .reset_index()
        .sort_values("run", ascending=False)
    )
    runs_table = mo.ui.table(
        summary, label="Select runs to plot (none selected = all)", page_size=8
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
def _(alt, history, metric, mo, runs_table):
    _picked = runs_table.value["run"] if len(runs_table.value) else history["run"]
    _data = history[history["run"].isin(_picked)]
    _chart = (
        alt.Chart(_data)
        .mark_line(point=True)
        .encode(
            x=alt.X("epoch:Q", title="Epoch"),
            y=alt.Y(f"{metric.value}:Q", title=metric.selected_key),
            color=alt.Color("run:N", title="Run"),
            tooltip=["run", "epoch", alt.Tooltip(f"{metric.value}:Q", format=".3f")],
        )
        .properties(height=320)
    )
    mo.ui.altair_chart(_chart)
    return


if __name__ == "__main__":
    app.run()
