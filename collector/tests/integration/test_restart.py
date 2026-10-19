"""A new interpreter recovers the encrypted jar and source high-water mark."""

from pathlib import Path
import subprocess
import sys
from google_maps_collector.config import Config
from google_maps_collector.service import Service
from google_maps_collector.store import EncryptedStore
from google_maps_collector.google_maps import parse_cookies
from test_google_maps import COOKIE
from test_service import Google


def test_new_interpreter_reuses_state(tmp_path):
    (tmp_path / "key").write_bytes(b"k" * 32)
    store = EncryptedStore(tmp_path / "session.json", tmp_path / "key")
    service = Service(Config(), store, Google(), lambda: 1800000001)
    service.import_cookies(parse_cookies(COOKIE))
    program = '''
from pathlib import Path
import sys
from google_maps_collector.config import Config
from google_maps_collector.service import Service
from google_maps_collector.store import EncryptedStore
root = Path(sys.argv[1])
service = Service(Config(), EncryptedStore(root/'session.json', root/'key'), None)
assert service.people['synthetic'].source_timestamp == 1800000000
assert len(service.cookies) == 1
assert service.status == 'starting'
print('recovered')
'''
    result = subprocess.run([sys.executable, "-c", program, str(tmp_path)],
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "recovered"
    assert "SYNTHETIC_SECRET" not in result.stdout + result.stderr
