"""Fail if entity policy or vendored upstream client drift outside the patch."""
import hashlib
import json
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[1]

def normalized(path):
    return path.read_bytes().replace(b"\r\n", b"\n")

def check():
    record = json.loads((ROOT / "docs/upstream-patch-boundary.json").read_text())
    directory = ROOT / "custom_components/google_maps"
    for name, expected in record["protected"].items():
        assert hashlib.sha256(normalized(directory / name)).hexdigest() == expected, name
    assert normalized(directory / "gm_loc_sharing.py") == normalized(
        ROOT / "collector/src/google_maps_collector/_upstream/gm_loc_sharing.py")
    changed = subprocess.check_output(["git", "diff", "--name-only", record["baseline"],
        "--", "custom_components/google_maps"], cwd=ROOT, text=True).splitlines()
    assert all(path.removeprefix("custom_components/google_maps/") in record["allowed_modified"] + record["added"] for path in changed), changed
    return record

if __name__ == "__main__":
    result = check()
    print(json.dumps({"upstream_guard": "passed", "baseline": result["baseline"],
        "protected_files": len(result["protected"])}))
