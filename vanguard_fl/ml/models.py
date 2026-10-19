from __future__ import annotations
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

class SmallCNN(nn.Module):
    def __init__(self, n_classes: int = 10) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(1, 16, 5)
        self.conv2 = nn.Conv2d(16, 32, 5)
        self.fc = nn.Linear(32 * 4 * 4, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.max_pool2d(F.relu(self.conv1(x)), 2)
        x = F.max_pool2d(F.relu(self.conv2(x)), 2)
        return self.fc(x.flatten(1))

def flatten_params(model: nn.Module) -> np.ndarray:
    return torch.cat([p.detach().reshape(-1) for p in model.parameters()]).cpu().numpy()

def load_flat_params(model: nn.Module, flat: np.ndarray) -> None:
    t = torch.as_tensor(np.asarray(flat, dtype = np.float32))
    i = 0
    with torch.no_grad():
        for p in model.parameters():
            n = p.numel()
            p.copy_(t[i: i + n].view_as(p))
            i += n
    if i != t.numel():
        raise ValueError(f"parameter vector length {t.numel()} != model size {i}")

def n_params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())
