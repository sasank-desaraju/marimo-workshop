# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "matplotlib",
#     "mlflow-skinny",
#     "mnist1d",
#     "torch",
# ]
# ///

import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import os
    import sys
    import time

    import marimo as mo
    import matplotlib.pyplot as plt
    import torch

    # Shared code lives in ../src, so every notebook uses the same Dataset and logger.
    _src = str(mo.notebook_dir().parent / "src")
    if _src not in sys.path:
        sys.path.insert(0, _src)
    from mnist1d_data import make_loaders
    from tracking import RunLogger

    return RunLogger, make_loaders, mo, os, plt, time, torch


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Train a small 1D CNN on MNIST-1D

    The same file works three ways:

    - **interactively**: pick settings below and press **Train**
    - **as a script**: `python notebooks/02_train.py -- --epochs 20 --lr 0.01`
    - **as a batch job**: `sbatch scripts/train.sbatch --epochs 20`

    Each run is logged to `runs/<run name>/metrics.csv`, and to MLflow as well
    when a server is configured. Open `03_results.py` to compare runs.
    """)
    return


@app.cell
def _(mo, os, torch):
    # Respect the Slurm CPU allocation instead of grabbing every core on the node.
    if hasattr(os, "sched_getaffinity"):
        torch.set_num_threads(len(os.sched_getaffinity(0)))

    if torch.cuda.is_available():
        device = torch.device("cuda")
        _note, _kind = f"GPU found: **{torch.cuda.get_device_name(0)}**.", "success"
    else:
        device = torch.device("cpu")
        _note = f"Running on **CPU** with {torch.get_num_threads()} threads. Plenty for MNIST-1D."
        _kind = "info"
    mo.callout(mo.md(_note), kind=_kind)
    return (device,)


@app.cell
def _(mo):
    # Command-line flags (after `--`) set the defaults; the widgets take over in the editor.
    _cli = mo.cli_args()
    _epochs = int(_cli.get("epochs", 15))
    epochs = mo.ui.slider(1, max(50, _epochs), value=_epochs, label="Epochs", show_value=True)
    lr = mo.ui.number(
        1e-4, 1.0, step=1e-4, value=float(_cli.get("lr", 0.01)), label="Learning rate"
    )
    batch_size = mo.ui.number(
        8, 4000, step=8, value=int(_cli.get("batch-size", 100)), label="Batch size"
    )
    seed = mo.ui.number(0, 2**31 - 1, value=int(_cli.get("seed", 0)), label="Seed")
    train_button = mo.ui.run_button(label="Train")
    mo.hstack([epochs, lr, batch_size, seed, train_button], justify="start", gap=1.5)
    return batch_size, epochs, lr, seed, train_button


@app.cell
def _(torch):
    class SmallConvNet(torch.nn.Module):
        """Three strided conv layers and a linear head: ~90% test accuracy in seconds."""

        def __init__(self, channels: int = 64, n_classes: int = 10):
            super().__init__()
            self.net = torch.nn.Sequential(
                torch.nn.Conv1d(1, channels, 5, stride=2, padding=2),  # 40 -> 20
                torch.nn.ReLU(),
                torch.nn.Conv1d(channels, channels, 3, stride=2, padding=1),  # 20 -> 10
                torch.nn.ReLU(),
                torch.nn.Conv1d(channels, channels, 3, stride=2, padding=1),  # 10 -> 5
                torch.nn.ReLU(),
                torch.nn.Flatten(),
                torch.nn.Linear(channels * 5, n_classes),
            )

        def forward(self, x):
            return self.net(x.unsqueeze(1))  # [B, 40] -> [B, 1, 40]

    return (SmallConvNet,)


@app.cell
def _(time, torch):
    def run_epoch(model, loader, device, opt=None):
        """One pass over `loader`; trains if an optimizer is given. Returns (loss, acc)."""
        model.train(opt is not None)
        total_loss = correct = seen = 0
        with torch.set_grad_enabled(opt is not None):
            for x, y in loader:
                x, y = x.to(device), y.to(device)
                logits = model(x)
                loss = torch.nn.functional.cross_entropy(logits, y)
                if opt is not None:
                    opt.zero_grad()
                    loss.backward()
                    opt.step()
                total_loss += loss.item() * len(y)
                correct += (logits.argmax(1) == y).sum().item()
                seen += len(y)
        return total_loss / seen, correct / seen

    def fit(model, train_loader, test_loader, device, epochs, lr, on_epoch):
        """Train for `epochs`, calling `on_epoch(epoch, metrics)` after each one."""
        model.to(device)
        opt = torch.optim.Adam(model.parameters(), lr=lr)
        start = time.perf_counter()
        for epoch in range(1, epochs + 1):
            train_loss, _ = run_epoch(model, train_loader, device, opt)
            test_loss, test_acc = run_epoch(model, test_loader, device)
            on_epoch(
                epoch,
                {
                    "train_loss": train_loss,
                    "test_loss": test_loss,
                    "test_acc": test_acc,
                    "seconds": time.perf_counter() - start,
                },
            )
        return model

    return (fit,)


@app.cell
def _(
    RunLogger,
    SmallConvNet,
    batch_size,
    device,
    epochs,
    fit,
    lr,
    make_loaders,
    mo,
    seed,
    torch,
    train_button,
):
    # In the editor, wait for the Train button. As a script, train right away.
    mo.stop(
        mo.running_in_notebook() and not train_button.value,
        mo.md("Pick settings and press **Train**."),
    )

    params = {
        "epochs": epochs.value,
        "lr": lr.value,
        "batch_size": int(batch_size.value),
        "seed": int(seed.value),
        "device": str(device),
    }
    torch.manual_seed(params["seed"])
    _loaders = make_loaders(batch_size=params["batch_size"])  # (train, test)
    history = []

    with (
        RunLogger(params) as run,
        mo.status.progress_bar(total=params["epochs"], title="Training") as _bar,
    ):
        print(f"Run {run.name} -> {run.where}", flush=True)

        def _on_epoch(epoch, metrics):
            run.log(epoch, metrics)
            history.append({"epoch": epoch, **metrics})
            print(
                f"epoch {epoch:3d}  train_loss {metrics['train_loss']:.3f}  "
                f"test_acc {metrics['test_acc']:.1%}  ({metrics['seconds']:.1f}s)",
                flush=True,  # keeps Slurm logs current
            )
            _bar.update()

        model = fit(SmallConvNet(), *_loaders, device, params["epochs"], params["lr"], _on_epoch)
        torch.save(model.state_dict(), run.dir / "model.pt")
    return (history,)


@app.cell
def _(history, mo, plt):
    _epochs = [h["epoch"] for h in history]
    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(10, 3))
    _ax1.plot(_epochs, [h["train_loss"] for h in history], marker="o", label="train")
    _ax1.plot(_epochs, [h["test_loss"] for h in history], marker="o", label="test")
    _ax1.set(title="Loss", xlabel="Epoch")
    _ax1.legend()
    _ax2.plot(_epochs, [h["test_acc"] for h in history], marker="o", color="tab:green")
    _ax2.set(title="Test accuracy", xlabel="Epoch", ylim=(0, 1))
    _fig.tight_layout()
    mo.vstack(
        [
            mo.md(
                f"Final test accuracy **{history[-1]['test_acc']:.1%}** after "
                f"{len(history)} epochs ({history[-1]['seconds']:.1f} s)."
            ),
            _fig,
        ]
    )
    return


if __name__ == "__main__":
    app.run()
