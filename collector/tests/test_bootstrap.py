from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import base64
import hashlib
import json
import pytest
from google_maps_collector.web import check_password

spec = spec_from_file_location("bootstrap_collector", Path(__file__).parents[2] / "tools/bootstrap_collector.py")
module = module_from_spec(spec)
spec.loader.exec_module(module)


def test_bootstrap_is_private_and_repeat_preserves_files(tmp_path, capsys):
    root = tmp_path / "collector"
    assert module.bootstrap(root, "synthetic-admin-password", assign_ownership=False)
    before = {name: (root / name).read_bytes() for name in module.FILES}
    assert len(before["store-key"]) == 32
    assert check_password("synthetic-admin-password", json.loads(before["admin-verifier"]))
    assert b"synthetic-admin-password" not in b"".join(before.values())
    assert not module.bootstrap(root, "", assign_ownership=False)
    assert all((root / name).read_bytes() == data for name, data in before.items())
    assert not capsys.readouterr().out
    assert (root / "data").is_dir() and (root / "broker-data").is_dir()
    users = dict(line.split(":", 1) for line in before["broker-passwords"].decode().splitlines())
    for user, file in (("collector", "mqtt-password"), ("homeassistant", "ha-password")):
        _, kind, iterations, salt, digest = users[user].split("$")
        assert kind == "7"
        actual = hashlib.pbkdf2_hmac("sha512", before[file], base64.b64decode(salt), int(iterations))
        assert actual == base64.b64decode(digest)


def test_partial_bootstrap_is_not_repaired_by_regeneration(tmp_path):
    root = tmp_path / "collector"
    root.mkdir()
    (root / "store-key").write_bytes(b"k" * 32)
    with pytest.raises(ValueError):
        module.bootstrap(root, "synthetic-admin-password", assign_ownership=False)
    assert (root / "store-key").read_bytes() == b"k" * 32
    assert len(list(root.iterdir())) == 1


def test_failed_bootstrap_cleans_only_staging(tmp_path, monkeypatch):
    def interrupted(*args):
        raise OSError("synthetic")
    monkeypatch.setattr(module.os, "rename", interrupted)
    with pytest.raises(OSError):
        module.bootstrap(tmp_path / "collector", "synthetic-admin-password", assign_ownership=False)
    assert not list(tmp_path.iterdir())


def test_container_definition_is_isolated():
    root = Path(__file__).parents[2]
    text = (root / "deploy/compose.yaml").read_text()
    for forbidden in ("privileged:", "network_mode:", "docker.sock", "/config:", "pid: host"):
        assert forbidden not in text
    assert '127.0.0.1:8787:8787' in text and '127.0.0.1:1883:1883' in text
    assert '10001:10001' in text and 'no-new-privileges:true' in text
    assert 'create_host_path: false' in text


def test_missing_key_cli_error_is_fixed_and_native_bind_is_loopback(tmp_path):
    import os
    import subprocess
    import sys
    from google_maps_collector.config import Config
    assert Config().management_bind == "127.0.0.1"
    result = subprocess.run([sys.executable, "-m", "google_maps_collector"],
        env={**os.environ, "KEY_FILE": str(tmp_path / "SYNTHETIC_SECRET")},
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 1
    assert result.stderr.strip() == "collector_startup_or_runtime_unavailable"
    assert "SYNTHETIC_SECRET" not in result.stdout + result.stderr
