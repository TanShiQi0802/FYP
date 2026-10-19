from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np

MOD = 1 << 32
HALF = 1 << 31

@dataclass
class Quantizer:
    clip: float
    n_clients: int
    modulus: int = MOD

    def __post_init__(self) -> None:
        self.refresh()

    def refresh(self, clip: float | None = None, n_clients: int | None = None) -> None:
        if clip is not None:
            self.clip = clip
        if n_clients is not None:
            self.n_clients = n_clients
        headroom = (self.modulus // 2) - 1
        denom = max(self.n_clients, 1) * max(self.clip, 1e-12)
        self.scale = max(1.0, math.floor(headroom / denom))

    def encode(self, vec: np.ndarray) -> np.ndarray:
        q = np.rint(np.asarray(vec, dtype=np.float64) * self.scale)
        limit = (self.modulus // 2) - 1
        if np.any(np.abs(q) > limit):
            raise ValueError("Quantized value exceeds the modulus. The gradient was not clipped")

        return np.mod(q.astype(np.int64), self.modulus).astype(np.uint32)

    def decode(self, agg: np.ndarray) -> np.ndarray:
        signed = agg.astype(np.int64)
        signed = np.where(signed >= HALF, signed - self.modulus, signed)
        return signed.astype(np.float64) / self.scale

def clip_l2(vec: np.ndarray, clip: float) -> tuple[np.ndarray, float, bool]:
    norm = float(np.linalg.norm(vec))
    if norm <= clip or norm == 0.0:
        return vec, norm, True
    return vec*(clip/norm), norm, False

class AdaptiveClipper:
    def __init__(self, initial: float, strategy: str = "quantile", target_quantile: float = 0.5, lr: float = 0.2, decay: float = 0.99, minimum: float = 1e-3) -> None:
        if strategy not in ("decay", "quantile", "fixed"):
            raise ValueError(f"Unknown clipping strategy {strategy!r}")
        self.clip = float(initial)
        self.strategy = strategy
        self.target = target_quantile
        self.lr = lr
        self.decay = decay
        self.minimum = minimum
        self.history = [self.clip]

    def update(self, fraction_width: float | None = None) -> float:
        if self.strategy == "fixed":
            pass
        elif self.strategy == "decay":
            self.clip = max(self.minimum, self.clip * self.decay)
        else:
            if fraction_width is None:
                raise ValueError("Quantile Strategy needs the aggrefated indicator")
            frac = min(max(fraction_width, 0.0), 1.0)
            self.clip = mqx(self.minimum, self.clip * math.exp(-self.lr*(frac - self.target)))

        self.history.append(self.clip)
        return self.clip
    