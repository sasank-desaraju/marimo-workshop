# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "numpy",
#     "pytest",  # importing n2_dataset.py compiles its tests
#     "torch",
# ]
# ///

"""Train a small 1D CNN on processed MNIST-1D.

Writes `runs/<timestamp>-<jobid or local>/{params.json,metrics.csv,model.pt}`.
The dataset class is imported from the n2_dataset.py notebook next to this file.

  uv run notebooks/n3_train.py --epochs 2
  sbatch scripts/train.sbatch --epochs 5
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import torch
from torch.utils.data import DataLoader

# Isn't this cool?!
from n2_dataset import MNIST1D  # the n2_dataset.py notebook

REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_PATH = REPO_ROOT / "data" / "processed" / "mnist1d.npz"  # written by n1
METRIC_FIELDS = ["epoch", "train_loss", "test_loss", "test_acc", "seconds"]


def pick_device() -> torch.device:
    """Use the Slurm CPU set, and a GPU when the job actually has one."""
    if hasattr(os, "sched_getaffinity"):
        torch.set_num_threads(len(os.sched_getaffinity(0)))
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


class SmallConvNet(torch.nn.Module):
    """Three strided convs. Input is `[batch, 40]`; the channel dim is added here."""

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
        return self.net(x.unsqueeze(1))


def run_epoch(model, loader, device, opt=None):
    """One pass over `loader`. Updates weights when `opt` is given."""
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
            batch = y.shape[0]
            total_loss += loss.item() * batch
            correct += (logits.argmax(1) == y).sum().item()
            seen += batch
    return total_loss / seen, correct / seen


def parse_args():
    parser = argparse.ArgumentParser(description="Train a 1D CNN on processed MNIST-1D.")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--lr", type=float, default=0.01)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--data",
        type=Path,
        default=None,
        help="Processed .npz (default: data/processed/mnist1d.npz from n2_dataset.py).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    device = pick_device()
    torch.manual_seed(args.seed)

    data_path = args.data if args.data is not None else PROCESSED_PATH
    train_loader = DataLoader(
        MNIST1D("train", data_path), batch_size=args.batch_size, shuffle=True
    )
    test_loader = DataLoader(MNIST1D("test", data_path), batch_size=1000)

    meta_path = data_path.with_name("metadata.json")
    normalize = None
    if meta_path.is_file():
        normalize = json.loads(meta_path.read_text()).get("normalize")

    job = os.environ.get("SLURM_JOB_ID", "local")
    run_dir = Path(os.environ.get("RUNS_DIR", REPO_ROOT / "runs"))
    run_dir = run_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{job}"
    run_dir.mkdir(parents=True, exist_ok=True)

    params = {
        "epochs": args.epochs,
        "lr": args.lr,
        "batch_size": args.batch_size,
        "seed": args.seed,
        "device": str(device),
        "data": str(data_path),
        "normalize": normalize,
    }
    (run_dir / "params.json").write_text(json.dumps(params, indent=2) + "\n")
    print(f"Run {run_dir.name} on {device} -> {run_dir}", flush=True)

    model = SmallConvNet().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    started = time.perf_counter()
    with (run_dir / "metrics.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=METRIC_FIELDS)
        writer.writeheader()
        handle.flush()  # n4_results.py can see the file before the first epoch lands
        for epoch in range(1, args.epochs + 1):
            train_loss, _train_acc = run_epoch(model, train_loader, device, opt)
            test_loss, test_acc = run_epoch(model, test_loader, device)
            seconds = time.perf_counter() - started
            writer.writerow(
                {
                    "epoch": epoch,
                    "train_loss": f"{train_loss:.6f}",
                    "test_loss": f"{test_loss:.6f}",
                    "test_acc": f"{test_acc:.6f}",
                    "seconds": f"{seconds:.3f}",
                }
            )
            handle.flush()
            print(
                f"epoch {epoch:3d}  train_loss {train_loss:.3f}  "
                f"test_acc {test_acc:.1%}  ({seconds:.1f}s)",
                flush=True,
            )
        torch.save(model.state_dict(), run_dir / "model.pt")
    print(f"Wrote {run_dir / 'model.pt'}", flush=True)


if __name__ == "__main__":
    main()
