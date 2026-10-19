import json
from pathlib import Path
import pytest
from google_maps_collector.store import EncryptedStore, StoreError


@pytest.fixture
def store(tmp_path):
    (tmp_path / "key").write_bytes(b"k" * 32)
    return EncryptedStore(tmp_path / "session.json", tmp_path / "key")


def test_roundtrip_restart_and_nonce(store):
    data = {"cookies": [{"value": "SYNTHETIC_SECRET"}], "timestamps": {"synthetic": 17}}
    assert store.load() is None
    store.save(data)
    first = store.path.read_bytes()
    assert b"SYNTHETIC_SECRET" not in first
    assert EncryptedStore(store.path, store.path.parent / "key").load() == data
    store.save(data)
    assert store.path.read_bytes() != first
    assert store.load() == data


@pytest.mark.parametrize("kind", ["tamper", "wrong-key", "version", "corrupt", "nonce", "missing-field"])
def test_fail_closed_without_erasure(store, kind):
    store.save({"canary": "SYNTHETIC_SECRET"})
    doc = json.loads(store.path.read_bytes())
    if kind == "wrong-key":
        (store.path.parent / "other").write_bytes(b"x" * 32)
        store = EncryptedStore(store.path, store.path.parent / "other")
    elif kind == "tamper":
        doc["ciphertext"] = "AAAA" + doc["ciphertext"][4:]
    elif kind == "version":
        doc["version"] = 999
    elif kind == "nonce":
        doc["nonce"] = "AAAA"
    elif kind == "missing-field":
        del doc["ciphertext"]
    if kind != "wrong-key":
        store.path.write_bytes(b"SYNTHETIC_SECRET" if kind == "corrupt" else json.dumps(doc).encode())
    before = store.path.read_bytes()
    with pytest.raises(StoreError) as error:
        store.load()
    assert "SYNTHETIC" not in str(error.value)
    assert store.path.read_bytes() == before


def test_interrupted_replace_preserves_previous(store, monkeypatch):
    import google_maps_collector.store as module
    store.save({"old": 1})
    def interrupted(*args):
        raise OSError("SYNTHETIC_SECRET")
    monkeypatch.setattr(module.os, "replace", interrupted)
    with pytest.raises(StoreError):
        store.save({"new": 2})
    assert store.load() == {"old": 1}
    assert not list(store.path.parent.glob(".pending-*"))


def test_invalid_data_preserves_previous(store):
    store.save({"old": 1})
    with pytest.raises(StoreError):
        store.save({"bad": float("nan")})
    assert store.load() == {"old": 1}


@pytest.mark.parametrize("key", [None, b"short", b"x" * 33])
def test_no_key_regeneration(tmp_path, key):
    path = tmp_path / "key"
    if key is not None:
        path.write_bytes(key)
    with pytest.raises(StoreError):
        EncryptedStore(tmp_path / "session.json", path)
    assert path.exists() == (key is not None)
    if key is not None:
        assert path.read_bytes() == key
