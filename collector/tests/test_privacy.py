

def test_privacy_across_google_management_mqtt_and_store(tmp_path, caplog):
    import json
    from starlette.testclient import TestClient
    from google_maps_collector.config import Config
    from google_maps_collector.google_maps import GoogleMaps, InvalidData, parse_cookies
    from google_maps_collector.mqtt import Publisher
    from google_maps_collector.service import Service
    from google_maps_collector.store import EncryptedStore
    from google_maps_collector.web import create_app, password_verifier
    from test_google_maps import Adapter, COOKIE, client
    from test_service import Google

    (tmp_path / "key").write_bytes(b"k" * 32)
    store = EncryptedStore(tmp_path / "session.json", tmp_path / "key")
    service = Service(Config(), store, Google(), lambda: 1800000001)
    service.import_cookies(parse_cookies(COOKIE))
    app = create_app(service, Config(), password_verifier("synthetic-admin-password"))
    with TestClient(app, base_url="http://127.0.0.1:8787") as browser:
        login = browser.post("/login", json={"password": "synthetic-admin-password"},
            headers={"Origin": "http://127.0.0.1:8787"})
        status = browser.get("/status")
        assert "SYNTHETIC_SECRET" not in login.text + status.text
        assert "latitude" not in status.text and "longitude" not in status.text
    calls = []
    Publisher(lambda topic, value, **kw: calls.append((topic, value))).sync(service.snapshot())
    assert "SYNTHETIC_SECRET" not in str(calls)
    for topic, body in calls:
        if not topic.endswith("/location"):
            assert "latitude" not in body and "longitude" not in body
    assert b"SYNTHETIC_SECRET" not in store.path.read_bytes()
    try:
        client(Adapter(body=b"SYNTHETIC_SECRET SYNTHETIC_PRIVATE_LOCATION")).poll(parse_cookies(COOKIE))
    except InvalidData as error:
        assert "SYNTHETIC" not in str(error)
    assert "SYNTHETIC_SECRET" not in caplog.text
    assert "SYNTHETIC_PRIVATE_LOCATION" not in caplog.text
