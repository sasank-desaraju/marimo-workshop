# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "altair",
#     "marimo",
#     "numpy",
#     "pandas",
#     "pytest",
#     "torch",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")

with app.setup:
    import json
    from pathlib import Path

    import numpy as np
    import torch
    from torch.utils.data import Dataset

    REPO_ROOT = Path(__file__).resolve().parents[1]
    PROCESSED_PATH = REPO_ROOT / "data" / "processed" / "mnist1d.npz"
    CLASSES = tuple(range(10))


@app.class_definition
class MNIST1D(Dataset):
    """One split of processed MNIST-1D.

    Each item is `(x, y)`: `x` is float32 with shape `[length]`, `y` an int64
    label. `path` defaults to the `.npz` written by `01_preprocess.py`.
    """

    def __init__(self, split: str = "train", path: str | Path | None = None):
        if split not in ("train", "test"):
            raise ValueError(f"split must be 'train' or 'test', got {split!r}")
        self.split = split
        self.path = Path(path) if path is not None else PROCESSED_PATH
        if not self.path.is_file():
            raise FileNotFoundError(
                f"No processed data at {self.path}. Run notebooks/01_preprocess.py first."
            )
        meta_path = self.path.with_name("metadata.json")
        self.meta = json.loads(meta_path.read_text()) if meta_path.is_file() else {}
        suffix = "" if split == "train" else "_test"
        raw_key = "x_raw" if split == "train" else "x_test_raw"
        # Copy out of the zip: the arrays are invalid after the file closes.
        with np.load(self.path) as blob:
            self.t = np.array(blob["t"])
            self.x = torch.as_tensor(np.array(blob["x" + suffix]), dtype=torch.float32)
            self.y = torch.as_tensor(np.array(blob["y" + suffix]), dtype=torch.long)
            self.x_raw = (
                torch.as_tensor(np.array(blob[raw_key]), dtype=torch.float32)
                if raw_key in blob.files
                else None
            )

    def __len__(self) -> int:
        return int(self.y.shape[0])

    def __getitem__(self, index):
        return self.x[index], self.y[index]

    def __repr__(self) -> str:
        return f"MNIST1D(split={self.split!r}, n={len(self)}, length={self.x.shape[1]})"


@app.cell
def _():
    import altair as alt
    import marimo as mo
    import pandas as pd

    return alt, mo, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Check the processed MNIST-1D set

    `MNIST1D` above is a normal PyTorch `Dataset`, exported from this notebook
    (`@app.class_definition`) so `03_train.py` can import it. It reads
    `data/processed/mnist1d.npz`. The plots below are a visual check that the
    examples and the preprocessing actually landed. The `test_*` functions at
    the bottom run with pytest:

    ```bash
    pytest notebooks/02_dataset.py
    ```

    The charts are Altair: you map DataFrame columns to `x`, `y`, and `color`,
    much like `aes()` in ggplot2. Wrapped in `mo.ui.altair_chart`, a chart's
    selection comes back to Python as `chart.value`.
    """)
    return


@app.cell
def _(mo):
    split = mo.ui.radio(["train", "test"], value="train", label="Split", inline=True)
    split
    return (split,)


@app.cell
def _(mo, split):
    if not PROCESSED_PATH.is_file():
        mo.stop(
            True,
            mo.callout(
                mo.md("No `data/processed/mnist1d.npz` yet. Run `01_preprocess.py` first."),
                kind="warn",
            ),
        )
    ds = MNIST1D(split.value)
    try:
        shown = ds.path.relative_to(REPO_ROOT)
    except ValueError:
        shown = ds.path
    mo.md(
        f"""
        `{ds}` from `{shown}`.

        | | |
        |---|---|
        | normalize | `{ds.meta.get("normalize", "?")}` |
        | augment (train) | `{ds.meta.get("augment", "?")}` |
        | filter | `{ds.meta.get("filter", "?")}` |
        | this split mean / std | **{float(ds.x.mean()):.4f}** / **{float(ds.x.std()):.4f}** |

        Z-score normalization lands near mean 0 and std 1 on the training split.
        """
    )
    return (ds,)


@app.cell
def _(mo):
    digit = mo.ui.dropdown([str(c) for c in CLASSES], value="3", label="Class")
    n_examples = mo.ui.slider(1, 12, value=6, label="Examples", show_value=True)
    mo.hstack([digit, n_examples], justify="start", gap=2)
    return digit, n_examples


@app.cell
def _(alt, digit, ds, mo, n_examples, pd):
    _idx = np.flatnonzero(ds.y.numpy() == int(digit.value))[: n_examples.value]
    _stages = [("After preprocessing", ds.x)]
    if ds.x_raw is not None:
        _stages.insert(0, ("Before (saved raw)", ds.x_raw))
    # Long format: one row per (stage, sample, t).
    _df = pd.concat(
        pd.DataFrame({"t": ds.t, "value": _x[_i].numpy(), "sample": _i, "stage": _name})
        for _name, _x in _stages
        for _i in _idx
    )
    _pick = alt.selection_point(fields=["sample"])
    examples = mo.ui.altair_chart(
        alt.Chart(_df)
        .mark_line(point=True)
        .encode(
            x="t:Q",
            y=alt.Y("value:Q", title=None),
            color=alt.Color("sample:N", title="Sample"),
            opacity=alt.condition(_pick, alt.value(0.9), alt.value(0.15)),
            column=alt.Column("stage:N", title=None, sort=[_name for _name, _ in _stages]),
        )
        .add_params(_pick)
        .properties(width=320, height=160)
        .resolve_scale(y="independent")
    )
    examples
    return (examples,)


@app.cell
def _(examples, mo):
    # `examples.value` holds the rows of whichever sample(s) you clicked.
    _picked = examples.value
    mo.stop(_picked.empty, mo.md("Click a line above (shift-click for more) to compare it here."))
    _stats = _picked.groupby(["sample", "stage"])["value"].agg(["mean", "std", "min", "max"])
    mo.ui.table(_stats.round(3).reset_index(), selection=None, label="Selected samples")
    return


@app.cell
def _(alt, ds, mo, pd):
    _counts = np.bincount(ds.y.numpy(), minlength=len(CLASSES))
    _chart = (
        alt.Chart(pd.DataFrame({"class": list(CLASSES), "count": _counts}))
        .mark_bar(color="gray")
        .encode(x=alt.X("class:O", axis=alt.Axis(labelAngle=0)), y="count:Q")
        .properties(width=640, height=140, title=f"Class balance ({ds.split})")
    )
    mo.vstack(
        [
            _chart,
            mo.md(f"Smallest class **{int(_counts.min())}**, largest **{int(_counts.max())}**."),
        ]
    )
    return


@app.cell
def _(mo):
    batch_size = mo.ui.slider(8, 256, step=8, value=32, label="Batch size", show_value=True)
    batch_size
    return (batch_size,)


@app.cell
def _(batch_size, ds, mo):
    from torch.utils.data import DataLoader

    _xb, _yb = next(iter(DataLoader(ds, batch_size=int(batch_size.value))))
    _steps = -(-len(ds) // int(batch_size.value))
    mo.md(
        f"""
        | tensor | shape | dtype |
        |---|---|---|
        | `x` | `{tuple(_xb.shape)}` | `{_xb.dtype}` |
        | `y` | `{tuple(_yb.shape)}` | `{_yb.dtype}` |
        | `x.unsqueeze(1)` (conv input) | `{tuple(_xb.unsqueeze(1).shape)}` | `{_xb.dtype}` |

        {len(ds)} examples at batch {int(batch_size.value)} is **{_steps}** steps per epoch.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Tests

    pytest collects these `test_*` functions directly off the file. They load
    the same processed arrays the plots do.
    """)
    return


@app.function
def test_sequence_length():
    # Break live: change 40 to 41, save, rerun `pytest notebooks/02_dataset.py`.
    x, _y = MNIST1D("train")[0]
    assert x.shape == (40,)


@app.function
def test_labels_are_digits():
    for split in ("train", "test"):
        labels = MNIST1D(split).y
        assert int(labels.min()) >= 0
        assert int(labels.max()) <= 9


@app.function
def test_counts_match_metadata():
    train, test = MNIST1D("train"), MNIST1D("test")
    assert len(train) == train.meta["n_train"]
    assert len(test) == test.meta["n_test"]
    assert train.x.shape[1] == test.x.shape[1] == train.meta["length"]


@app.function
def test_zscore_centers_training_set():
    data = MNIST1D("train")
    if data.meta.get("normalize") != "zscore":
        import pytest

        pytest.skip("processed file was not z-scored")
    values = data.x.numpy()
    assert abs(float(values.mean())) < 1e-3
    assert abs(float(values.std()) - 1) < 1e-3


@app.function
def test_transform_changes_values():
    data = MNIST1D("train")
    if data.x_raw is None:
        import pytest

        pytest.skip("processed file has no raw copy")
    untouched = (
        data.meta.get("normalize", "none") == "none"
        and data.meta.get("augment", "none") == "none"
        and data.meta.get("filter", "none") == "none"
    )
    if untouched:
        import pytest

        pytest.skip("pipeline was asked to make no changes")
    assert not torch.allclose(data.x, data.x_raw)


if __name__ == "__main__":
    app.run()
