from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
import numpy as np

_FIELD = 32
_KEY = 32
_SIG = 64

@dataclass
class KeyAdvert:
    client_id: int
    mask_public: bytes
    comm_public: bytes
    signing_public: bytes
    signature: bytes
    beacon_commitment: bytes = b""

    def nbytes(self) -> int:
        return 4 + _KEY*3 + _SIG + len(self.beacon_commitment)

@dataclass
class SetupBroadcast:
    round_no: int
    roster: List[int]
    beacon: bytes
    degree: int
    threshold: int
    adverts: Dict[int, KeyAdvert]
    min_cohort: int = 0
    min_survival_fraction: float = 0.0
    reveals: Dict[int, bytes] = field(default_factory=dict)
    signature: bytes = b""

    def nbytes(self) -> int:
        n = len(self.roster)
        return (8 + 4*n + len(self.beacon) + 8 + 8 + 4 + n*(4 + _KEY*3 + _SIG) + sum(len(r) for r in self.reveals.values()) + _SIG)

@dataclass
class ShareMessage:
    sender: int
    receiver: int
    round_no: int
    ciphertext: bytes

    def nbytes(self) -> int:
        return 12 + len(self.ciphertext)

@dataclass
class ModelBroadcast:
    round_no: int
    weights: np.ndarray
    model_hash: bytes
    sparsity_seed: bytes
    clip: float

    def nbytes(self) -> int:
        return 8 + self.weights.size*4 + len(self.model_hash) + len(self.sparsity_seed) + 8

@dataclass
class MaskedPayload:
    client_id: int
    round_no: int
    model_hash: bytes
    vector: np.ndarray
    signature: bytes

    def nbytes(self) -> int:
        return 8 + len(self.model_hash) + self.vector.size*4 + _SIG

@dataclass
class RosterAnnouncement:
    round_no: int
    survivors: List[int]
    dropped: List[int]
    signature: bytes

    def nbytes(self) -> int:
        return 8 + 4*(len(self.survivors) + len(self.dropped)) + _SIG

@dataclass
class ShareRelease:
    client_id: int
    round_no: int
    self_seed_shares: Dict[int, int]
    mask_key_shares: Dict[int, int]
    signature: bytes = b""

    def nbytes(self) -> int:
        n = len(self.self_seed_shares) + len(self.mask_key_shares)
        return 8 + n*(4 + _FIELD) + _SIG

@dataclass
class RoundResult:
    round_no: int
    ok: bool
    aggregate: np.ndarray | None = None
    n_included: int = 0
    fraction_within_clip: float | None = None
    reason: str = ""
    stats: Dict[str, float] = field(default_factory=dict)
    