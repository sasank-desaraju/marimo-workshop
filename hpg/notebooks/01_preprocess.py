# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "altair",
#     "marimo",
#     "mnist1d",
#     "numpy",
#     "pandas",
# ]
# ///

import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")

with app.setup:
    import json
    from pathlib import Path

    import altair as alt
    import marimo as mo
    import numpy as np
    import pandas as pd

    # Paths in --out are relative to the hpg/ folder, not the shell's cwd.
    REPO_ROOT = Path(__file__).resolve().parents[1]
    OUT_NAME = "mnist1d.npz"


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Preprocess MNIST-1D

    Generate the dataset locally, then smooth, augment, and normalize it.
    The same controls are command-line flags, so this file is both a notebook
    and a batch step:

    ```bash
    uv run notebooks/01_preprocess.py --out data/processed --normalize zscore --filter smooth
    ```

    `02_dataset.py` reads `data/processed/mnist1d.npz` and `metadata.json`.
    """)
    return


@app.cell
def _():
    cli = mo.cli_args()
    choices = {
        "normalize": ("none", "zscore", "minmax"),
        "augment": ("none", "noise", "shift"),
        "filter": ("none", "smooth"),
    }

    def pick(name, default):
        value = cli.get(name, default)
        value = default if value == "" else str(value)
        if value not in choices[name]:
            options = ", ".join(choices[name])
            raise ValueError(f"--{name} must be one of {options} (got {value!r})")
        return value

    normalize = mo.ui.dropdown(
        list(choices["normalize"]), value=pick("normalize", "zscore"), label="Normalize"
    )
    augment = mo.ui.dropdown(
        list(choices["augment"]), value=pick("augment", "none"), label="Augment train"
    )
    filter_kind = mo.ui.dropdown(
        list(choices["filter"]), value=pick("filter", "smooth"), label="Filter"
    )
    seed = mo.ui.number(0, 2**31 - 1, value=int(cli.get("seed", 42)), label="Seed")
    out_dir = mo.ui.text(value=str(cli.get("out", "data/processed")), label="Output directory")
    save = mo.ui.run_button(label="Save arrays")
    mo.vstack(
        [
            mo.hstack([normalize, augment, filter_kind, seed], justify="start", gap=1.5),
            mo.hstack([out_dir, save], justify="start", gap=1.5),
        ]
    )
    return augment, filter_kind, normalize, out_dir, save, seed


@app.cell
def _(seed):
    # MNIST-1D is built from templates (about a second). Kept separate so
    # changing the filter or the normalization does not rebuild it.
    from mnist1d.data import get_dataset_args, make_dataset

    data_args = get_dataset_args()
    data_args.seed = int(seed.value)
    raw = make_dataset(data_args)
    return (raw,)


@app.cell
def _():
    def smooth(values, width=5):
        """Moving average along the sequence, same length out."""
        pad = width // 2
        padded = np.pad(values, ((0, 0), (pad, pad)), mode="edge")
        windows = np.lib.stride_tricks.sliding_window_view(padded, width, axis=1)
        return windows.mean(axis=-1)

    def transform(raw, *, normalize, augment, filter_kind, seed):
        """Filter both splits, augment train only, normalize from train stats."""
        rng = np.random.default_rng(seed)
        x = np.array(raw["x"], dtype=np.float64, copy=True)
        x_test = np.array(raw["x_test"], dtype=np.float64, copy=True)

        if filter_kind == "smooth":
            x = smooth(x)
            x_test = smooth(x_test)
        if augment == "noise":
            x = x + rng.normal(0.0, 0.1, size=x.shape)
        elif augment == "shift":
            for row, shift in zip(x, rng.integers(-4, 5, size=len(x))):
                row[:] = np.roll(row, int(shift))

        # Fit on the training split, then apply that same map to test.
        fit = {}
        if normalize == "zscore":
            mean = float(x.mean())
            std = float(x.std()) or 1.0
            x = (x - mean) / std
            x_test = (x_test - mean) / std
            fit = {"mean": mean, "std": std}
        elif normalize == "minmax":
            lo, hi = float(x.min()), float(x.max())
            span = (hi - lo) or 1.0
            x = (x - lo) / span
            x_test = (x_test - lo) / span
            fit = {"min": lo, "max": hi}

        arrays = {
            "x": x.astype(np.float32),
            "y": np.array(raw["y"], dtype=np.int64, copy=True),
            "x_test": x_test.astype(np.float32),
            "y_test": np.array(raw["y_test"], dtype=np.int64, copy=True),
            "t": np.array(raw["t"], dtype=np.float32, copy=True),
            "x_raw": np.array(raw["x"], dtype=np.float32, copy=True),
            "x_test_raw": np.array(raw["x_test"], dtype=np.float32, copy=True),
        }
        return arrays, fit

    return (transform,)


@app.cell
def _(augment, filter_kind, normalize, raw, seed, transform):
    arrays, fit = transform(
        raw,
        normalize=normalize.value,
        augment=augment.value,
        filter_kind=filter_kind.value,
        seed=int(seed.value),
    )
    return arrays, fit


@app.cell
def _():
    digit = mo.ui.slider(0, 9, value=3, label="Class", show_value=True)
    n_examples = mo.ui.slider(1, 8, value=5, label="Examples", show_value=True)
    mo.hstack([digit, n_examples], justify="start", gap=2)
    return digit, n_examples


@app.cell
def _(arrays, digit, n_examples):
    idx = np.flatnonzero(arrays["y"] == int(digit.value))[: n_examples.value]
    # Long format: one row per (stage, sample, t).
    _df = pd.concat(
        pd.DataFrame({"t": arrays["t"], "value": arrays[_key][_i], "sample": _i, "stage": _stage})
        for _stage, _key in (("Raw", "x_raw"), ("Processed", "x"))
        for _i in idx
    )
    _chart = (
        alt.Chart(_df)
        .mark_line(opacity=0.8)
        .encode(
            x="t:Q",
            y=alt.Y("value:Q", title=None),
            color=alt.Color("sample:N", legend=None),
            column=alt.Column("stage:N", title=None, sort=["Raw", "Processed"]),
        )
        .properties(width=320, height=160)
        .resolve_scale(y="independent")
    )
    mo.vstack(
        [
            mo.md(
                f"Train, after the pipeline: mean **{float(arrays['x'].mean()):.3f}**, "
                f"std **{float(arrays['x'].std()):.3f}** "
                f"({arrays['x'].shape[0]} × {arrays['x'].shape[1]})."
            ),
            _chart,
        ]
    )
    return


@app.cell
def _(arrays, augment, filter_kind, fit, normalize, out_dir, save, seed):
    # In the editor, wait for Save. As a script, write immediately.
    mo.stop(
        mo.running_in_notebook() and not save.value,
        mo.md(
            "Nothing written yet. Press **Save arrays** to write the current settings to "
            f"`{out_dir.value}/{OUT_NAME}`."
        ),
    )
    dest = Path(out_dir.value)
    if not dest.is_absolute():
        dest = REPO_ROOT / dest
    dest.mkdir(parents=True, exist_ok=True)
    npz_path = dest / OUT_NAME
    meta_path = dest / "metadata.json"
    np.savez_compressed(npz_path, **arrays)
    meta = {
        "seed": int(seed.value),
        "normalize": normalize.value,
        "augment": augment.value,
        "filter": filter_kind.value,
        "n_train": int(arrays["x"].shape[0]),
        "n_test": int(arrays["x_test"].shape[0]),
        "length": int(arrays["x"].shape[1]),
        **fit,
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    print(f"Wrote {npz_path}", flush=True)
    try:
        shown = npz_path.relative_to(REPO_ROOT)
    except ValueError:
        shown = npz_path
    mo.callout(mo.md(f"Wrote `{shown}` and `{meta_path.name}`."), kind="success")
    return


if __name__ == "__main__":
    app.run()
