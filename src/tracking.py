"""Where training runs are recorded, and how to read them back.

Every run writes `runs/<run name>/metrics.csv` (plus `params.json`), which
needs no setup and works offline. If an MLflow server is configured, the same
params and metrics are logged there too. `02_train.py` writes, `03_results.py`
reads.

The MLflow server is found, in order, from:
  1. the MLFLOW_TRACKING_URI environment variable (marimo also loads it from .env)
  2. mlruns/server.env, written by scripts/mlflow_server.sbatch while it runs
"""

from __future__ import annotations

import csv
import json
import os
import warnings
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = Path(os.environ.get("RUNS_DIR", REPO_ROOT / "runs"))
SERVER_ENV = REPO_ROOT / "mlruns" / "server.env"
EXPERIMENT = os.environ.get("MLFLOW_EXPERIMENT_NAME", "mnist1d-workshop")

# If the server has gone away, fail in seconds instead of retrying for minutes.
os.environ.setdefault("MLFLOW_HTTP_REQUEST_MAX_RETRIES", "0")
os.environ.setdefault("MLFLOW_HTTP_REQUEST_TIMEOUT", "5")


def tracking_uri() -> str | None:
    """The MLflow tracking URI to use, or None to stick with CSV."""
    if uri := os.environ.get("MLFLOW_TRACKING_URI"):
        return uri
    if SERVER_ENV.exists():
        for line in SERVER_ENV.read_text().splitlines():
            key, _, value = line.partition("=")
            if key.strip() == "MLFLOW_TRACKING_URI" and value.strip():
                return value.strip()
    return None


def new_run_name() -> str:
    """Timestamp plus Slurm job id, e.g. `20261022-104512-123456` (or `-local`)."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{os.environ.get('SLURM_JOB_ID', 'local')}"


class RunLogger:
    """Log params and per-epoch metrics to CSV, and to MLflow when available.

    Use as a context manager:

        with RunLogger({"lr": 0.01}) as run:
            run.log(epoch=1, metrics={"test_acc": 0.5})
    """

    def __init__(self, params: dict, run_name: str | None = None):
        self.name = run_name or new_run_name()
        self.dir = RUNS_DIR / self.name
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "params.json").write_text(json.dumps(params, indent=2))
        self._file = (self.dir / "metrics.csv").open("w", newline="")
        self._writer: csv.DictWriter | None = None
        self.mlflow = self._start_mlflow(params)

    def _start_mlflow(self, params: dict):
        uri = tracking_uri()
        if uri is None:
            return None
        try:
            import mlflow

            mlflow.set_tracking_uri(uri)
            mlflow.set_experiment(EXPERIMENT)
            mlflow.start_run(run_name=self.name)
            mlflow.log_params(params)
            return mlflow
        except Exception as err:  # noqa: BLE001 - a run should never die over logging
            warnings.warn(f"MLflow at {uri} unavailable ({err}); logging to CSV only.")
            return None

    @property
    def where(self) -> str:
        """Human-readable summary of where this run is being logged."""
        target = f"{self.dir}/metrics.csv"
        return target + (f" + MLflow at {tracking_uri()}" if self.mlflow else "")

    def log(self, epoch: int, metrics: dict[str, float]) -> None:
        row = {"epoch": epoch, **metrics}
        if self._writer is None:
            self._writer = csv.DictWriter(self._file, fieldnames=list(row))
            self._writer.writeheader()
        self._writer.writerow(row)
        self._file.flush()  # lets 03_results.py watch a run while it trains
        if self.mlflow is not None:
            self.mlflow.log_metrics(metrics, step=epoch)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_) -> None:
        self._file.close()
        if self.mlflow is not None:
            self.mlflow.end_run(status="FAILED" if exc_type else "FINISHED")


# ---- reading runs back (used by 03_results.py) --------------------------------


def load_csv_runs():
    """All runs under runs/ as `(history, params)` pandas DataFrames."""
    import pandas as pd

    histories, params = [], []
    for metrics_csv in sorted(RUNS_DIR.glob("*/metrics.csv")):
        run = metrics_csv.parent.name
        try:
            df = pd.read_csv(metrics_csv)
        except pd.errors.EmptyDataError:  # run just started, no epochs yet
            continue
        histories.append(df.assign(run=run))
        params_json = metrics_csv.parent / "params.json"
        params.append({"run": run, **json.loads(params_json.read_text())})
    history = pd.concat(histories, ignore_index=True) if histories else pd.DataFrame()
    return history, pd.DataFrame(params)


def load_mlflow_runs(uri: str, max_runs: int = 50):
    """Runs from the MLflow experiment as `(history, params)` pandas DataFrames."""
    import mlflow
    import pandas as pd

    client = mlflow.MlflowClient(tracking_uri=uri)
    experiment = client.get_experiment_by_name(EXPERIMENT)
    if experiment is None:
        return pd.DataFrame(), pd.DataFrame()

    rows, params = [], []
    runs = client.search_runs(
        [experiment.experiment_id],
        order_by=["attributes.start_time DESC"],
        max_results=max_runs,
    )
    for r in runs:
        name = r.info.run_name
        params.append({"run": name, "status": r.info.status, **r.data.params})
        by_epoch: dict[int, dict] = {}
        for key in r.data.metrics:
            for m in client.get_metric_history(r.info.run_id, key):
                by_epoch.setdefault(m.step, {})[key] = m.value
        rows += [{"run": name, "epoch": e, **v} for e, v in sorted(by_epoch.items())]
    return pd.DataFrame(rows), pd.DataFrame(params)
