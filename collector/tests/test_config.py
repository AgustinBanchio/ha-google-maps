import pytest
from google_maps_collector.config import Config


@pytest.mark.parametrize("settings", [
    {"poll_seconds": 0}, {"poll_seconds": True}, {"freshness_seconds": 299},
    {"freshness_seconds": 3601}, {"upload_bytes": 1048577},
    {"management_origin": "http://example.test:8787"},
])
def test_invalid_settings(settings):
    with pytest.raises(ValueError):
        Config(**settings)


def test_defaults_and_private_paths():
    assert Config().freshness_seconds == 0
    assert "/run/secrets" not in repr(Config())


def test_upstream_defaults_and_optional_safety_settings():
    assert Config().max_gps_accuracy == 1000 and Config().include_account is True
    assert Config(freshness_seconds=900).freshness_seconds == 900
    for settings in ({"max_gps_accuracy": -1}, {"include_account": "true"}, {"freshness_seconds": True}):
        with pytest.raises(ValueError): Config(**settings)
