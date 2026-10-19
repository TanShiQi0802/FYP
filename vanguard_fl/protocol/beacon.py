from __future__ import annotations
import hashlib
import secrets
from typing import Callable, Dict, Optional

def randk_seed(beacon: bytes, round_no: int) -> bytes:
    h = hashlib.sha256()
    h.update(b"vanguard-randk-seed|")
    h.update(beacon)
    h.update(b"randk")
    h.update(int(round_no).to_bytes(8, "big"))
    return h.digest()

class ExternalBeacon:
    name = "external"
    needs_reveals = False

    def __init__(self, provider: Callable[[int], bytes]) -> None:
        self._provider = provider

    def for_round(self, round_no: int) -> bytes:
        h = hashlib.sha256()
        h.update(b"vanguard-beacon-external|")
        h.update(int(round_no).to_bytes(8, "big"))
        h.update(self._provider(round_no))
        return h.digest()

    def verify(self, round_no: int, beacon: bytes, reveals: Optional[Dict[int, bytes]] = None, commitments: Optional[Dict[int, bytes]] = None) -> bool:
        return beacon == self.for_round(round_no)

class CommitRevealBeacon:
    name = "commit_reveal"
    needs_reveals = True

    @staticmethod
    def commit(rho: bytes, nonce: bytes) -> bytes:
        h = hashlib.sha256()
        h.update(b"vanguard-beacon-commit|")
        h.update(rho)
        h.update(nonce)
        return h.digest()

    @staticmethod
    def combine(round_no: int, reveals: Dict[int, bytes]) -> bytes:
        acc = bytearray(32)
        for cid in sorted(reveals):
            rho = reveals[cid][:32]
            for i in range(32):
                acc[i] ^= rho[i]
        h = hashlib.sha256()
        h.update(b"vanguard-beacon-commitreveal|")
        h.update(int(round_no).to_bytes(8, "big"))
        h.update(bytes(acc))
        return h.digest()

    def for_round(self, round_no: int, reveals: Optional[Dict[int, bytes]] = None) -> bytes:
        if not reveals:
            raise ValueError("Commit-reeval beacon needs the clients' reveals")
        return self.combine(round_no, reveals)

    def verify(self, round_no: int, beacon: bytes, reveals: Optional[Dict[int, bytes]] = None, commitments: Optional[Dict[int, bytes]] = None) -> bool:
        if not reveals or commitments is None:
            return False
        for cid, blob in reveals.items():
            expected = commitments.get(cid)
            if expected is None or self.commit(blob[:32], blob[32:64]) != expected:
                return False
        return beacon == self.combine(round_no, reveals)