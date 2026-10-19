# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "matplotlib",
#     "mnist1d",
#     "numpy",
#     "torch",
# ]
# ///

import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys

    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    from torch.utils.data import DataLoader

    # Shared code lives in ../src, so every notebook uses the same Dataset and logger.
    _src = str(mo.notebook_dir().parent / "src")
    if _src not in sys.path:
        sys.path.insert(0, _src)
    from mnist1d_data import CLASSES, MNIST1D

    return CLASSES, DataLoader, MNIST1D, mo, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Build and inspect a PyTorch Dataset

    Before training anything, look at the data. This notebook builds the
    [MNIST-1D](https://github.com/greydanus/mnist1d) `Dataset` that
    `02_train.py` uses and checks what a model will actually receive:
    what examples look like, whether classes are balanced, and what shape a
    batch has.
    """)
    return


@app.cell
def _(mo):
    split = mo.ui.radio(["train", "test"], value="train", label="Split", inline=True)
    split
    return (split,)


@app.cell
def _(MNIST1D, mo, split):
    ds = MNIST1D(split.value)
    _x, _y = ds[0]
    mo.md(
        f"""
        `{ds!r}`

        One item is a pair `(x, y)`: `x` is a `{_x.dtype}` tensor of shape
        `{tuple(_x.shape)}`, `y` is a `{_y.dtype}` label, here `{int(_y)}`.
        """
    )
    return (ds,)


@app.cell
def _(CLASSES, mo):
    digit = mo.ui.dropdown([str(c) for c in CLASSES], value="3", label="Class")
    n_examples = mo.ui.slider(1, 20, value=8, label="Examples", show_value=True)
    mo.hstack([digit, n_examples], justify="start", gap=2)
    return digit, n_examples


@app.cell
def _(digit, ds, n_examples, np, plt):
    _idx = np.flatnonzero(ds.y.numpy() == int(digit.value))[: n_examples.value]
    _fig, _ax = plt.subplots(figsize=(8, 2.8))
    for _i in _idx:
        _ax.plot(ds.t, ds.x[_i], lw=1, alpha=0.7)
    _ax.set_title(f"{len(_idx)} examples of class {digit.value} ({ds.split})")
    _ax.set_xlabel("t")
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(CLASSES, ds, mo, np, plt):
    _counts = np.bincount(ds.y.numpy(), minlength=len(CLASSES))
    _fig, _ax = plt.subplots(figsize=(8, 2.2))
    _ax.bar(CLASSES, _counts, color="tab:gray")
    _ax.set_xticks(CLASSES)
    _ax.set_title("Class balance")
    _fig.tight_layout()
    mo.vstack(
        [
            _fig,
            mo.md(f"Smallest class has **{_counts.min()}** examples, largest **{_counts.max()}**."),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## What the model sees

    A `DataLoader` stacks items into batches. A 1D CNN wants a channel
    dimension too, so `02_train.py` adds one with `x.unsqueeze(1)`.
    """)
    return


@app.cell
def _(mo):
    batch_size = mo.ui.slider(8, 512, step=8, value=100, label="Batch size", show_value=True)
    batch_size
    return (batch_size,)


@app.cell
def _(DataLoader, batch_size, ds, mo):
    _xb, _yb = next(iter(DataLoader(ds, batch_size=batch_size.value, shuffle=True)))
    mo.md(
        f"""
        | tensor | shape | dtype |
        |---|---|---|
        | `x` batch | `{tuple(_xb.shape)}` | `{_xb.dtype}` |
        | `y` batch | `{tuple(_yb.shape)}` | `{_yb.dtype}` |
        | `x.unsqueeze(1)` (CNN input) | `{tuple(_xb.unsqueeze(1).shape)}` | `{_xb.dtype}` |

        {len(ds)} examples at batch size {batch_size.value} is
        **{-(-len(ds) // batch_size.value)}** batches per epoch.
        """
    )
    return


if __name__ == "__main__":
    app.run()
