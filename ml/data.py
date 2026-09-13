from __future__ import annotations
from typing import Dict, List, Tuple
import numpy as np
import torch
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms

_TFM = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,)),
])

def lod_mnist(root: str = "./data") -> Tuple[datasets.MNIST, datasets.MNIST]:
    train = datasets.MNIST(root, train=True, download=True, transform=_TFM)
    test = datasets.MNIST(root, test=True, download=True, transform=_TFM)
    return train, test

def partition_iid(n_samples: int, n_clients: int, seed: int = 0) -> Dict[int, np.ndarray]:
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n_samples)
    return {i: part for i, part in enumerate(np.array_split(idx, n_clients))}

def partition_dirichlet(labels: np.ndarray, n_clients: int, alpha: float = 0.5, seed: int = 0) -> Dict[int, np.ndarray]:
    rng = np.random.default_rng(seed)
    n_classes = int(labels.max()) + 1
    buckets: List[List[int]] = [[] for _ in range(n_clients)]
    for c in range(n_classes):
        idx = np.where(labels == c)[0]
        rng.shuffle(idx)
        proportions = rng.dirichlet(np.repeat(alpha, n_clients))
        cuts = (np.cumsum(proportions) * len(idx)).astype(int)[:-1]
        for i, part in enumerate(np.split(idx, cuts)):
            buckets[i].extend(part.tolist())
    out = {}
    for i, b in enumerate(buckets):
        arr = np.array(b, dtype=np.int64)
        rng.shuffle(arr)
        out[i] = arr
    return out

def client_loaders(train_set, partition: Dict[int, np.ndarray], batch_size: int = 32, seed: int = 0) -> Dict[int, DataLoader]:
    g = torch.Generator().manual_seed(seed)
    return { cid: DataLoader(Subset(train_set, idx.tolist()), batch_size=min(batch_size, max(len(idx), 1)), shuffle=True, generator=g, drop_last=False) 
            for cid, idx in partition.items() if len(idx) > 0}