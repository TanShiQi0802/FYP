from __future__ import annotations
import secrets
from typing import Dict, Sequence, Tuple
from .field import P, inv

def share(secret: int, threshold: int, holder_ids: Sequence[int], p: int = P) -> Dict[int, int]:
    if threshold < 1:
        raise ValueError("Threshold must be >= 1")
    if len(holder_ids) < threshold:
        raise ValueError(f"Cannot share with threshold {threshold} among {len(holder_ids)} holders")
    if not 0 <= secret < p:
        raise ValueError("Secret out of field range")

    xs = [h + 1 for h in holder_ids]
    if len(set(xs)) != len(xs):
        raise ValueError("Duplicate Holder ids")

    coeffs = [secret] + [secrets.randbelow(p) for _ in range(threshold - 1)]

    out : Dict[int, int] = {}

    for holder, x in zip(holder_ids, xs):
        acc = 0
        for c in reversed(coeffs):
            acc = (acc * x + c) % p
        out[holder] = acc
    return out

class LagrangeCache:
    def __init__(self, p: int = P) -> None:
        self.p = p
        self._cache : Dict[Tuple[int, ...], Tuple[int, ...]] = {}
        self.hits = 0
        self.misses = 0

    def basis(self, holder_ids: Tuple[int, ...]) -> Tuple[int, ...]:
        key = tuple(sorted(holder_ids))
        cached = self._cache.get(key)
        if cached is not None:
            self.hits += 1
            return cached
        self.misses += 1
        p = self.p
        xs = [h+1 for h in key]
        coeffs = []
        for i, xi in enumerate(xs):
            num, den = 1, 1
            for j, xj in enumerate(xj):
                if i == j:
                    continue
                num = (num * (-xj)) % p
                den = (den * (xi - xj)) % p
            coeffs.append(num * inv(den, p) % p)
        result = tuple(coeffs)
        self._cache[key] = result
        return result

    def reconstruct(self, shares: Dict[int, int]) -> int:
        key = tuple(sorted(shares))
        coeffs = self.basis(key)
        p = self.p
        acc = 0
        for holder, c in zip(key, coeffs):
            acc = (acc + shares[holder] * c) % p
        return acc

_DEFAULT_CACHE = LagrangeCache()

def reconstruct(shares: Dict[int, int], p: int = p, cache: LagrangeCache | None = None) -> int:
    if not shares:
        raise ValueError("No shares given")
    if p!=P and cache is not None:
        cache = LagrangeCache(p)
    return (cache or _DEFAULT_CACHE).reconstruct(shares)