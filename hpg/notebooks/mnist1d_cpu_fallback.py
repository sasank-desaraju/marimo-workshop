# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "altair",
#     "marimo",
#     "mnist1d",
#     "numpy",
#     "pandas",
#     "torch",
# ]
# ///

import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Fallback demo: train a tiny model on CPU

    The backup plan for the HiPerGator demo, in one self-contained file: no
    GPU, no cluster, no other files from this repo, and no internet once the
    packages are installed. The dataset is
    [MNIST-1D](https://github.com/greydanus/mnist1d), generated on the fly
    from a few templates, so there is nothing to download.

    Training takes well under a minute on a laptop CPU. If a GPU is
    available, the same code uses it automatically.

    Run it anywhere:

    - `uvx marimo edit --sandbox mnist1d_cpu_fallback.py`
    - `uv run mnist1d_cpu_fallback.py --epochs 20` (plain script)
    """)
    return


@app.cell
def _():
    import time

    import altair as alt
    import numpy as np
    import pandas as pd
    import torch
    from mnist1d.data import get_dataset_args, make_dataset

    return alt, get_dataset_args, make_dataset, np, pd, time, torch


@app.cell
def _(mo, torch):
    if torch.cuda.is_available():
        device = torch.device("cuda")
        device_note = f"GPU found: **{torch.cuda.get_device_name(0)}**."
        kind = "success"
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        device = torch.device("mps")
        device_note = "Apple GPU (MPS) found."
        kind = "success"
    else:
        device = torch.device("cpu")
        device_note = (
            f"No GPU found, running on **CPU** with {torch.get_num_threads()} threads. "
            "That's fine for this model."
        )
        kind = "info"
    mo.callout(mo.md(device_note), kind=kind)
    return (device,)


@app.cell
def _(mo):
    # Defaults can be overridden from the command line, e.g. `--epochs 20`.
    _cli = mo.cli_args()
    epochs = mo.ui.slider(1, 50, value=int(_cli.get("epochs", 15)), label="Epochs", show_value=True)
    hidden = mo.ui.dropdown(
        ["32", "64", "128"], value=str(_cli.get("hidden", "64")), label="Channels"
    )
    lr = mo.ui.dropdown(
        ["0.003", "0.01", "0.03"], value=str(_cli.get("lr", "0.01")), label="Learning rate"
    )
    train_button = mo.ui.run_button(label="Train")
    mo.hstack([epochs, hidden, lr, train_button], justify="start", gap=2)
    return epochs, hidden, lr, train_button


@app.cell
def _(get_dataset_args, make_dataset):
    data_args = get_dataset_args()
    data = make_dataset(data_args)
    return (data,)


@app.cell
def _(alt, data, mo, np, pd):
    _first = [int(np.where(data["y"] == _digit)[0][0]) for _digit in range(10)]
    _df = pd.concat(
        pd.DataFrame({"t": data["t"], "value": data["x"][_idx], "digit": _digit})
        for _digit, _idx in enumerate(_first)
    )
    _chart = (
        alt.Chart(_df)
        .mark_line()
        .encode(x=alt.X("t:Q", axis=None), y=alt.Y("value:Q", axis=None))
        .properties(width=150, height=80)
        .facet(alt.Facet("digit:N", title=None), columns=5)
        .properties(title="One training example per class")
    )
    mo.vstack(
        [
            mo.md(
                f"**{len(data['x'])}** training and **{len(data['x_test'])}** test "
                f"sequences, each {data['x'].shape[1]} points long, 10 classes."
            ),
            _chart,
        ]
    )
    return


@app.cell
def _(torch):
    class SmallConvNet(torch.nn.Module):
        """A 1D CNN that reaches roughly 90%+ test accuracy on MNIST-1D."""

        def __init__(self, channels: int = 64, n_classes: int = 10):
            super().__init__()
            self.net = torch.nn.Sequential(
                torch.nn.Conv1d(1, channels, 5, stride=2, padding=2),
                torch.nn.ReLU(),
                torch.nn.Conv1d(channels, channels, 3, stride=2, padding=1),
                torch.nn.ReLU(),
                torch.nn.Conv1d(channels, channels, 3, stride=2, padding=1),
                torch.nn.ReLU(),
                torch.nn.Flatten(),
                torch.nn.LazyLinear(n_classes),
            )

        def forward(self, x):
            return self.net(x.unsqueeze(1))

    return (SmallConvNet,)


@app.cell
def _(time, torch):
    def train(model, data, device, epochs=15, lr=0.01, batch_size=100, on_epoch=None):
        """Plain training loop. Returns per-epoch history as a dict of lists."""
        x = torch.tensor(data["x"], dtype=torch.float32, device=device)
        y = torch.tensor(data["y"], dtype=torch.long, device=device)
        x_test = torch.tensor(data["x_test"], dtype=torch.float32, device=device)
        y_test = torch.tensor(data["y_test"], dtype=torch.long, device=device)

        model = model.to(device)
        model(x[:1])  # materialize the lazy layer before building the optimizer
        opt = torch.optim.Adam(model.parameters(), lr=lr)
        loss_fn = torch.nn.CrossEntropyLoss()
        history = {"train_loss": [], "test_acc": [], "seconds": []}
        start = time.perf_counter()

        for _epoch in range(epochs):
            model.train()
            perm = torch.randperm(len(x), device=device)
            total = 0.0
            for i in range(0, len(x), batch_size):
                idx = perm[i : i + batch_size]
                opt.zero_grad()
                loss = loss_fn(model(x[idx]), y[idx])
                loss.backward()
                opt.step()
                total += loss.item() * len(idx)
            model.eval()
            with torch.no_grad():
                acc = (model(x_test).argmax(1) == y_test).float().mean().item()
            history["train_loss"].append(total / len(x))
            history["test_acc"].append(acc)
            history["seconds"].append(time.perf_counter() - start)
            if on_epoch is not None:
                on_epoch(_epoch, history)
        return model, history

    return (train,)


@app.cell
def _(
    SmallConvNet,
    data,
    device,
    epochs,
    hidden,
    lr,
    mo,
    torch,
    train,
    train_button,
):
    # In the editor, wait for the Train button. As a script, train right away.
    mo.stop(
        mo.running_in_notebook() and not train_button.value,
        mo.md("Pick settings and press **Train**."),
    )
    torch.manual_seed(0)
    with mo.status.progress_bar(total=epochs.value, title="Training") as _bar:
        _model, history = train(
            SmallConvNet(channels=int(hidden.value)),
            data,
            device,
            epochs=epochs.value,
            lr=float(lr.value),
            on_epoch=lambda *_: _bar.update(),
        )
    print(
        f"Done on {device}: test accuracy {history['test_acc'][-1]:.1%} "
        f"in {history['seconds'][-1]:.1f}s"
    )
    return (history,)


@app.cell
def _(alt, history, mo, pd):
    _ep = range(1, len(history["train_loss"]) + 1)
    _base = (
        alt.Chart(pd.DataFrame(history).assign(epoch=list(_ep)))
        .mark_line(point=True)
        .encode(x=alt.X("epoch:Q", title="Epoch"))
        .properties(width=320, height=180)
    )
    _loss = _base.encode(y=alt.Y("train_loss:Q", title=None)).properties(title="Training loss")
    _acc = _base.encode(
        y=alt.Y("test_acc:Q", title=None, scale=alt.Scale(domain=[0, 1])),
        color=alt.value("green"),
    ).properties(title="Test accuracy")
    _chart = _loss | _acc
    mo.vstack(
        [
            mo.md(
                f"Final test accuracy **{history['test_acc'][-1]:.1%}** after "
                f"{len(_ep)} epochs ({history['seconds'][-1]:.1f} s)."
            ),
            _chart,
        ]
    )
    return


if __name__ == "__main__":
    app.run()
