"""Exercise the maintained HA patch against a synthetic upstream entity update."""
from pathlib import Path
import subprocess
import tempfile
import tarfile
from io import BytesIO
import json
ROOT=Path(__file__).resolve().parents[1]
BASE="b2132123d46c47e5761d5d91cc08ca6b712fe6c1"

def run(args, cwd, **kwargs):
    return subprocess.check_output(args,cwd=cwd,stderr=subprocess.DEVNULL,**kwargs)

def main():
    patch=run(["git","diff","--binary",BASE,"--","custom_components/google_maps"],ROOT)
    archive=run(["git","archive",BASE,"custom_components/google_maps"],ROOT)
    with tempfile.TemporaryDirectory(prefix="maps-upstream-check-") as directory:
        target=Path(directory)
        with tarfile.open(fileobj=BytesIO(archive)) as source:source.extractall(target,filter="data")
        run(["git","init","-q"],target)
        def commit(message):
            run(["git","add","."],target)
            run(["git","-c","user.name=Synthetic upstream test","-c","user.email=synthetic@example.invalid","commit","-qm",message],target)
        commit("synthetic baseline")
        entity=target/"custom_components/google_maps/device_tracker.py"
        entity.write_bytes(entity.read_bytes()+b"\nUPSTREAM_UPDATE_CANARY = True\n")
        commit("synthetic upstream tracking change")
        run(["git","apply","--3way","--index"],target,input=patch)
        assert b"UPSTREAM_UPDATE_CANARY = True" in entity.read_bytes()
        assert (target/"custom_components/google_maps/collector_client.py").is_file()
        assert "CollectorClient" in (target/"custom_components/google_maps/coordinator.py").read_text()
    print(json.dumps({"synthetic_upstream_rebase":"passed","updated_original_entity_preserved":True}))

if __name__=="__main__":main()
