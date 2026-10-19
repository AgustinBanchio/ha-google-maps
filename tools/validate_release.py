"""Validate source metadata and require observed immutable image evidence for release."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")


def source_checks():
    lock = tomllib.loads((ROOT / "collector/uv.lock").read_text())
    project = tomllib.loads((ROOT / "collector/pyproject.toml").read_text())
    packages = {item["name"]: item for item in lock["package"]}
    for dependency in project["project"]["dependencies"]:
        name, version = dependency.split("==")
        if packages[name]["version"] != version:
            raise ValueError("dependency pin mismatch")
    for package in packages.values():
        if "registry" not in package["source"]:
            continue
        files = ([package["sdist"]] if "sdist" in package else []) + package.get("wheels", [])
        if not files or not all(HASH.fullmatch(item["hash"]) for item in files):
            raise ValueError("missing distribution hashes")
    for name in ("deploy/Dockerfile", "deploy/test/Dockerfile"):
        for line in (ROOT / name).read_text().splitlines():
            if line.startswith("FROM ") and "@sha256:" not in line:
                raise ValueError("unpinned build image")
    return hashlib.sha256((ROOT / "collector/uv.lock").read_bytes()).hexdigest()


def check_wheel(path):
    with zipfile.ZipFile(path) as wheel:
        for name in wheel.namelist():
            if not (name.startswith("google_maps_collector/") or ".dist-info/" in name):
                raise ValueError("unexpected wheel path")
            if any(word in name for word in (".local", "__pycache__", "cookies.txt", "session.json")):
                raise ValueError("private file in wheel")
            body = wheel.read(name)
            if any(canary in body for canary in (b"SYNTHETIC_SECRET", b"SYNTHETIC_PRIVATE_LOCATION")):
                raise ValueError("canary in wheel")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def release_checks(record, lock_hash):
    data = json.loads(record.read_text())
    if data["lock_sha256"] != lock_hash or not re.fullmatch(r"[0-9a-f]{40}", data["source_revision"]):
        raise ValueError("release source metadata mismatch")
    image = data["image"]
    local_id = HASH.fullmatch(image) is not None
    if not local_id and not re.fullmatch(r"[a-zA-Z0-9._:/-]+@sha256:[0-9a-f]{64}", image):
        raise ValueError("release requires immutable image reference")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
    if dirty or revision != data["source_revision"]:
        raise ValueError("release requires the exact clean source revision")
    observed = json.loads(subprocess.check_output(["docker", "image", "inspect", image],
        cwd=ROOT, text=True, stderr=subprocess.DEVNULL))[0]
    if ((observed.get("Id") != image if local_id else image not in observed.get("RepoDigests", []))
            or observed["Config"]["Labels"].get("org.opencontainers.image.revision") != revision
            or observed["Config"]["User"] != "10001:10001"):
        raise ValueError("image evidence mismatch")
    wheel = Path(data["wheel"])
    if not wheel.is_absolute():
        wheel = ROOT / wheel
    if check_wheel(wheel) != data["wheel_sha256"]:
        raise ValueError("wheel hash mismatch")
    if data.get("arm64_startup") != "passed" or data.get("container_recovery") != "passed":
        raise ValueError("container acceptance evidence missing")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-only", action="store_true", help="validate metadata without claiming release acceptance")
    parser.add_argument("--record", type=Path, default=ROOT / ".local/release.json")
    parser.add_argument("--wheel", type=Path, help="also inspect a built wheel")
    args = parser.parse_args()
    try:
        lock_hash = source_checks()
        if args.wheel:
            check_wheel(args.wheel)
        if not args.source_only:
            release_checks(args.record, lock_hash)
        print("source_metadata_passed" if args.source_only else "release_metadata_passed")
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, zipfile.BadZipFile):
        print("release_validation_incomplete", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
