"""Authenticated, atomic persistence. A missing or invalid key never gets replaced."""

import base64
import json
import os
from pathlib import Path
import secrets
import tempfile
from threading import RLock

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

VERSION = 1
AAD = b"google-maps-collector/store/v1"
MAX_STORE_BYTES = 8 * 1024 * 1024


class StoreError(Exception):
    def __init__(self):
        super().__init__("credential_store_unavailable")


def atomic_write(path: Path, data: bytes) -> None:
    """Commit in one rename, with same-directory temporary and fsync on POSIX."""
    temporary = None
    try:
        descriptor, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
        with os.fdopen(descriptor, "wb") as output:
            os.chmod(temporary, 0o600)
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        temporary = None
        if os.name == "posix":
            directory = os.open(path.parent, os.O_DIRECTORY | os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


class EncryptedStore:
    def __init__(self, path: Path, key_file: Path):
        self.path = path
        self.lock = RLock()
        try:
            with key_file.open("rb") as source:
                key = source.read(33)
            if len(key) != 32:
                raise StoreError()
            self._cipher = AESGCM(key)
        except OSError:
            raise StoreError() from None

    def load(self) -> dict | None:
        with self.lock:
            try:
                with self.path.open("rb") as source:
                    raw = source.read(MAX_STORE_BYTES + 1)
                if len(raw) > MAX_STORE_BYTES:
                    raise StoreError()
                document = json.loads(raw)
                if type(document) is not dict or (type(document.get("version")) is not int or document["version"] != VERSION):
                    raise StoreError()
                nonce = base64.b64decode(document["nonce"], validate=True)
                encrypted = base64.b64decode(document["ciphertext"], validate=True)
                if len(nonce) != 12:
                    raise StoreError()
                data = json.loads(self._cipher.decrypt(nonce, encrypted, AAD))
                if type(data) is not dict:
                    raise StoreError()
                return data
            except FileNotFoundError:
                return None
            except (OSError, ValueError, TypeError, KeyError, InvalidTag, RecursionError):
                raise StoreError() from None

    def save(self, data: dict) -> None:
        with self.lock:
            try:
                if type(data) is not dict:
                    raise StoreError()
                plaintext = json.dumps(data, allow_nan=False, separators=(",", ":")).encode()
                nonce = secrets.token_bytes(12)
                ciphertext = self._cipher.encrypt(nonce, plaintext, AAD)
                encoded = json.dumps({"version": VERSION,
                    "nonce": base64.b64encode(nonce).decode(),
                    "ciphertext": base64.b64encode(ciphertext).decode()}).encode()
                if len(encoded) > MAX_STORE_BYTES:
                    raise StoreError()
                atomic_write(self.path, encoded)
            except (OSError, ValueError, TypeError):
                raise StoreError() from None
