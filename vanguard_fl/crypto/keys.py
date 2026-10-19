from __future__ import annotations
import secrets
from dataclasses import dataclass
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (Ed25519PrivateKey, Ed25519PublicKey,)
from cryptography.hazmat.primitives.asymmetric.x25519 import (X25519PrivateKey, X25519PublicKey,)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .field import P, field_to_bytes
from .prg import derive_key

@dataclass
class KeyPair:
    private: X25519PrivateKey
    public_bytes: bytes

    @property
    def private_bytes(self) -> bytes:
        return self.private.private_bytes_raw()

    @property
    def private_int(self) -> int:
        return int.from_bytes(self.private_bytes, "big")

@dataclass
class SigningKeyPair:
    private: Ed25519PrivateKey
    public_bytes: bytes

def _gen_x25519_in_field() -> KeyPair:
    while True:
        priv = X25519PrivateKey.generate()
        if int.from_bytes(priv.private_bytes_raw(), "big") < P:
            return KeyPair(priv, priv.public_key().public_bytes_raw())

def gen_mask_keypair() -> KeyPair:
    return _gen_x25519_in_field()

def gen_comm_keypair() -> KeyPair:
    return _gen_x25519_in_field()

def gen_signing_keypair() -> SigningKeyPair:
    priv = Ed25519PrivateKey.generate()
    return SigningKeyPair(priv, priv.public_key().public_bytes_raw())

def keypair_from_private_int(x: int) -> KeyPair:
    priv = X25519PrivateKey.from_private_bytes(field_to_bytes(x))
    return KeyPair(priv, priv.public_key().public_bytes_raw())

def random_field_seed() -> bytes:
    while True:
        b = secrets.token_bytes(32)
        if int.from_bytes(b, "big") < P:
            return b

def dh_agree(private: X25519PrivateKey, peer_public: bytes, label: bytes) -> bytes:
    shared = private.exchange(X25519PublicKey.from_public_bytes(peer_public))
    return derive_key(shared, label)

def sign(sk: SigningKeyPair, message: bytes) -> bytes:
    return sk.private.sign(message)

def verify(public_bytes: bytes, signature: bytes, message: bytes) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(public_bytes).verify(signature, message)
        return True
    except InvalidSignature:
        return False

def encrypt_for(comm_private: X25519PrivateKey, peer_comm_public: bytes, plaintext: bytes, associated_data: bytes) -> bytes:
    key = dh_agree(comm_private, peer_comm_public, b"vanguard-share-enc")
    nonce = secrets.token_bytes(12)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, associated_data)

def decrypt_from(comm_private: X25519PrivateKey, peer_comm_public: bytes, ciphertext: bytes, associated_data: bytes) -> bytes:
    key = dh_agree(comm_private, peer_comm_public, b"vanguard-share_enc")
    nonce, body = ciphertext[:12], ciphertext[12:]
    return AESGCM(key).decrypt(nonce, body, associated_data)
