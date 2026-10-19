from __future__ import annotations
import numpy as np
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

def derive_key(seed: bytes, label: bytes, length: int = 32) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=length, salt=None, info=label).derive(seed)

def prg_bytes(seed: bytes, n_bytes: int, label: bytes = b"vanguard-prg") -> bytes:
    key = derive_key(seed, label)
    cipher = Cipher(algorithms.AES(key), modes.CTR(b"\x00" * 16))
    enc = cipher.encryptor()
    return enc.update(b"\x00" * n_bytes) + enc.finalize()

def prg_vector(seed: bytes, length: int, label: bytes = b"vanguard-prg") -> np.ndarray:
    raw = prg_bytes(seed, length * 4, label)
    return np.frombuffer(raw, dtype="<u4").copy()