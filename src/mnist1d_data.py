"""MNIST-1D as a PyTorch Dataset.

Shared by 01_dataset_explore.py (to look at the data) and 02_train.py (to train
on it), so both notebooks see exactly the same thing.

MNIST-1D (https://github.com/greydanus/mnist1d) is a tiny stand-in for MNIST:
each example is a 1D sequence of 40 points drawn from one of ten digit-like
templates, then shifted, scaled, and noised. It is generated locally in about a
second, so there is nothing to download and it trains fine on a CPU.
"""

from functools import lru_cache

import torch
from torch.utils.data import DataLoader, Dataset

CLASSES = tuple(range(10))


@lru_cache(maxsize=4)
def generate(seed: int = 42) -> dict:
    """Generate the raw MNIST-1D arrays. Cached, so each seed is built once."""
    from mnist1d.data import get_dataset_args, make_dataset

    args = get_dataset_args()  # defaults: 4000 train / 1000 test, length 40
    args.seed = seed
    return make_dataset(args)


class MNIST1D(Dataset):
    """MNIST-1D examples as `(x, y)` pairs: `x` is float32 `[40]`, `y` an int64 label."""

    def __init__(self, split: str = "train", seed: int = 42):
        if split not in ("train", "test"):
            raise ValueError(f"split must be 'train' or 'test', got {split!r}")
        data = generate(seed)
        suffix = "" if split == "train" else "_test"
        self.split = split
        self.t = data["t"]  # the shared "time" axis, handy for plotting
        self.x = torch.as_tensor(data["x" + suffix], dtype=torch.float32)
        self.y = torch.as_tensor(data["y" + suffix], dtype=torch.long)

    def __len__(self) -> int:
        return len(self.y)

    def __getitem__(self, i):
        return self.x[i], self.y[i]

    def __repr__(self) -> str:
        return f"MNIST1D(split={self.split!r}, n={len(self)}, length={self.x.shape[1]})"


def make_loaders(batch_size: int = 100, seed: int = 42, num_workers: int = 0):
    """Train and test DataLoaders. The data is tiny, so workers rarely help."""
    train = DataLoader(
        MNIST1D("train", seed), batch_size=batch_size, shuffle=True, num_workers=num_workers
    )
    test = DataLoader(MNIST1D("test", seed), batch_size=1000, num_workers=num_workers)
    return train, test
