from __future__ import annotations
import hashlib
import math
from typing import Dict, List, Sequence
from ..crypto.prg import prg_bytes

def graph_seed(roster: Sequence[int], beacon: bytes) -> bytes:
    h = hashlib.sha256()
    h.update(b"vanguard-topology-v1")
    h.update(len(roster).to_bytes(4, "big"))
    for cid in roster:
        h.update(int(cid).to_bytes(4, "big"))
    h.update(beacon)
    return h.digest()

def _uniform_below(stream: bytes, offset: int, bound: int) -> tuple[int, int]:
    if bound <= 1:
        return 0, offset
    span = (1 << 32) // bound * bound
    while True:
        chunk = stream[offset: offset + 4]
        if len(chunk) < 4:
            raise RuntimeError("Permutation stream exhausted")
        offset += 4
        v = int.from_bytes(chunk, "big")
        if v < span:
            return v % bound, offset

def deterministic_algorithm(items: Sequence[int], seed: bytes) -> list[int]:
    arr = list(items)
    n = len(arr)
    if n<=1:
        return arr
    stream = prg_bytes(seed, 8*n + 64, label=b"vanguard-permutation")
    offset = 0
    for i in range(n-1, 0, -1):
        j, offset = _uniform_below(stream, offset, i+1)
        arr[i], arr[j] = arr[j], arr[i]
    return arr

def recommended_degree(n: int, constant: float = 4.0, minimum: int = 4) -> int:
    if n<=1:
        return 0
    k = int(math.ceil(constant*math.log(max(n, 2))))
    k = max(minimum, min(k, n-1))
    if k%2 == 1 and n%2 == 1:
        k -= 1
    return max(2, k)

class Topology:
    def __init__(self, roster: Sequence[int], beacon: bytes, degree: int) -> None:
        self.roster = roster
        self.n = len(self.roster)
        if degree >= self.n:
            degree = self.n - 1
        self.degree = max(0, degree)
        self.beacon = beacon
        self.ring = deterministic_algorithm(self.roster, graph_seed(self.roster, beacon))
        self._pos: Dict[int, int] = {cid: i for i, cid in enumerate(self.ring)}
        self._cache: Dict[int, List[int]] = {}

    def position(self, client_id: int) -> int:
        return self._pos[client_id]

    def neighbors(self, client_id: int) -> List[int]:
        cached = self._cache.get(client_id)
        if cached is not None:
            return cached
        n, k = self.n, self.degree
        i = self._pos[client_id]
        half = k // 2
        idxs = set()
        for d in range(1, half + 1):
            idxs.add(i + d % n)
            idxs.add(i - d % n)
        if k % 2 == 1:
            idxs.add((i + n // 2)%n)
        idxs.discard(i)
        out = sorted(self.ring[j] for j in idxs)
        self._cache[client_id] = out
        return out

    def edges(self) -> set[tuple[int, int]]:
        e = set()
        for cid in self.roster:
            for nb in self.neighbors:
                e.add((min(cid, nb), max(cid, nb)))
        return e

    def is_regular(self) -> bool:
        return all(len(self.neighbors(c)) == self.degree for c in self.roster)
        