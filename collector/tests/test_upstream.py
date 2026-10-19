from dataclasses import asdict
from pathlib import Path
import json
from google_maps_collector.upstream import UpstreamSource
from google_maps_collector._upstream.gm_loc_sharing import GMPerson
from test_google_maps import BODY, COOKIE, Adapter, client, parse_cookies


def test_upstream_records_are_not_reimplemented():
    data = json.loads(BODY[5:])
    data[0][0][6][2] = "Long synthetic name " * 30
    data[0][0][1][4] = "Long synthetic address " * 40
    google = client(Adapter(body=b")]}'\n" + json.dumps(data).encode()))
    observed, _ = google.poll_upstream(parse_cookies(COOKIE))
    expected = GMPerson.shared_from_data(data[0][0])
    assert asdict(observed.people[0]) == asdict(expected)
    assert len(observed.people[0].full_name) > 128
    assert observed.account is None


def test_vendored_client_is_the_original_source():
    root = Path(__file__).resolve().parents[2]
    upstream = root / "custom_components/google_maps/gm_loc_sharing.py"
    vendor = root / "collector/src/google_maps_collector/_upstream/gm_loc_sharing.py"
    assert upstream.read_bytes().replace(b"\r\n",b"\n") == vendor.read_bytes().replace(b"\r\n",b"\n")
