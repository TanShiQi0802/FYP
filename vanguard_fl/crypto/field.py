from __future__ import annotations

P = 2**256 - 189
P_BYTES = 32

def inv(a: int, p: int = P) -> int:
    a %= p
    if a == 0:
        raise ZeroDivisionError("no inverse for 0 in a prime field")
    return pow(a, p - 2, p)

def bytes_to_field(b: bytes, p: int = P) -> int:
    x = int.from_bytes(b, "big")
    if x >= p:
        raise ValueError("value does not fit in the field without wrapping")
    return x

def field_to_bytes(x: int, length: int = P_BYTES) -> bytes:
    return int(x).to_bytes(length, "big")