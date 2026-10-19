from dataclasses import replace
import json
from types import SimpleNamespace
from google_maps_collector.google_maps import Person
from google_maps_collector.mqtt import Publisher, contact_id, MQTT, BIRTH, GLOBAL


PERSON = Person("SYNTHETIC_PRIVATE_ID", 0.5, 0.25, 25, 1800000000, 73)


def snapshot(person=PERSON, available=True, status="ready"):
    return {"people": [person], "available": {person.id} if available else set(), "status": status}


def test_discovery_contract_and_schema():
    calls = []
    publisher = Publisher(lambda *args, **kw: calls.append((args, kw)))
    publisher.sync(snapshot())
    topics = {args[0]: args[1] for args, kw in calls}
    key = contact_id(PERSON.id)
    discovery = json.loads(topics[f"homeassistant/device_tracker/google_maps_collector/{key}/config"])
    assert discovery["source_type"] == "gps"
    assert discovery["visible_by_default"] is True
    assert discovery["enabled_by_default"] is True
    assert discovery["availability_mode"] == "all"
    location = json.loads(topics[f"google_maps_collector/{key}/location"])
    assert set(location) == {"latitude", "longitude", "gps_accuracy", "source_timestamp",
        "full_name", "nickname", "entity_picture", "address", "country_code",
        "last_seen", "battery_level", "battery_charging"}
    assert location["source_timestamp"] == PERSON.source_timestamp
    assert all(kw == {"qos": 1, "retain": True} for _, kw in calls)
    assert "SYNTHETIC_PRIVATE_ID" not in str(calls)
    assert "SYNTHETIC_SECRET" not in str(calls)


def test_battery_change_updates_tracker_without_changing_source_fix():
    calls = []
    publisher = Publisher(lambda topic, payload, **kw: calls.append((topic, payload)))
    publisher.sync(snapshot())
    calls.clear()
    publisher.sync(snapshot(replace(PERSON, battery=40)))
    location = json.loads(next(value for topic, value in calls if topic.endswith("/location")))
    assert location["latitude"] == PERSON.latitude and location["source_timestamp"] == PERSON.source_timestamp
    assert location["battery_level"] == 40
    assert any(topic.endswith("/battery") and value == "40" for topic, value in calls)
    calls.clear()
    publisher.sync(snapshot(replace(PERSON, source_timestamp=PERSON.source_timestamp - 1)))
    assert not any(topic.endswith("/location") for topic, _ in calls)


def test_stale_auth_failure_and_resync():
    calls = []
    publisher = Publisher(lambda topic, payload, **kw: calls.append((topic, payload)))
    publisher.sync(snapshot())
    calls.clear()
    publisher.sync(snapshot(available=False, status="credential_required"), force=True)
    assert any(t.endswith("/availability") and p == "offline" for t, p in calls)
    assert ("google_maps_collector/session", "OFF") in calls
    assert not any(t.endswith("/location") for t, _ in calls)
    calls.clear()
    publisher.sync(snapshot(), force=True)
    locations = [json.loads(p) for t, p in calls if t.endswith("/location")]
    assert locations[0]["source_timestamp"] == PERSON.source_timestamp


def test_exact_birth_subscription_and_will(tmp_path):
    from google_maps_collector.config import Config
    path = tmp_path / "password"
    path.write_text("SYNTHETIC_BROKER_PASSWORD")
    mqtt = MQTT(Config(mqtt_password_file=path))
    assert mqtt.client._will_topic == GLOBAL.encode()
    assert mqtt.client._will_payload == b"offline"
    subscriptions, publishes = [], []
    fake = SimpleNamespace(subscribe=lambda *a, **kw: subscriptions.append(a),
        publish=lambda *a, **kw: publishes.append(a))
    mqtt._connected(fake, None, None, 0, None)
    assert subscriptions == [(BIRTH,)]
    assert mqtt.resync.is_set()
    mqtt.resync.clear()
    mqtt._message(None, None, SimpleNamespace(topic="forbidden/command", payload=b"online"))
    assert not mqtt.resync.is_set()
    mqtt._message(None, None, SimpleNamespace(topic=BIRTH, payload=b"online"))
    assert mqtt.resync.is_set()


def test_google_names_update_discovery_without_new_gps_fix():
    calls = []
    publisher = Publisher(lambda topic, payload, **kw: calls.append((topic, payload)))
    publisher.sync(snapshot(replace(PERSON, display_name="Synthetic Alice")))
    key = contact_id(PERSON.id)
    discovery = json.loads(next(payload for topic, payload in calls if topic.endswith(f"/{key}/config")))
    assert discovery["device"]["name"] == "Google Maps Synthetic Alice"
    assert discovery["visible_by_default"] is True
    assert discovery["unique_id"] == "google_maps_collector_" + key
    calls.clear()
    publisher.sync(snapshot(replace(PERSON, display_name="Synthetic Alice Updated")))
    assert any(topic.endswith("/config") for topic, payload in calls)
    location = json.loads(next(p for t, p in calls if t.endswith("/location")))
    assert location["source_timestamp"] == PERSON.source_timestamp
    assert location["full_name"] == "Synthetic Alice Updated"
    assert all("Synthetic Alice" not in topic for topic, payload in calls)
    assert "SYNTHETIC_SECRET" not in str(calls)


def test_all_upstream_attributes_and_independent_metadata_updates():
    calls = []
    publisher = Publisher(lambda topic, payload, **kw: calls.append((topic, payload)))
    person = replace(PERSON, display_name="Synthetic Alice", nickname="Alice",
        picture_url="https://lh3.googleusercontent.com/synthetic-picture",
        address="Synthetic address", country_code="ZZ", battery_charging=True)
    publisher.sync(snapshot(person))
    location = json.loads(next(p for t, p in calls if t.endswith("/location")))
    details = json.loads(next(p for t, p in calls if t.endswith("/details")))
    assert location.items() >= details.items()
    assert details == {"full_name": "Synthetic Alice", "nickname": "Alice",
        "entity_picture": person.picture_url, "address": "Synthetic address",
        "country_code": "ZZ", "battery_level": 73, "battery_charging": True,
        "last_seen": "2027-01-15T08:00:00+00:00"}
    calls.clear()
    publisher.sync(snapshot(replace(person, battery=42, battery_charging=False)))
    updated = json.loads(next(p for t, p in calls if t.endswith("/location")))
    assert updated["source_timestamp"] == person.source_timestamp
    assert updated["latitude"] == person.latitude and updated["battery_charging"] is False
    details = json.loads(next(p for t, p in calls if t.endswith("/details")))
    assert details["battery_level"] == 42 and details["battery_charging"] is False
    assert "SYNTHETIC_SECRET" not in str(calls)


def test_connectivity_sensor_reports_poll_failures_separately_from_trackers():
    calls = []
    publisher = Publisher(lambda topic, payload, **kw: calls.append((topic, payload)))
    publisher.sync(snapshot())
    calls.clear()
    publisher.sync(snapshot(status="network_failure"))
    assert ("google_maps_collector/session", "OFF") in calls
    assert not any(t.endswith("/availability") and p == "offline" for t,p in calls)


def test_tracker_picture_is_discovery_configuration_and_refreshes_on_change_or_removal():
    # HA filters entity_picture out of JSON attributes. Its MqttEntity reads the
    # supported discovery field instead, including on discovery_update.
    calls = []
    publisher = Publisher(lambda topic, payload, **kw: calls.append((topic, payload)))
    key = contact_id(PERSON.id)
    topic = f"homeassistant/device_tracker/google_maps_collector/{key}/config"
    first = replace(PERSON, display_name="Synthetic Alice",
        picture_url="https://lh3.googleusercontent.com/synthetic-picture-a")
    publisher.sync(snapshot(first))
    original = json.loads(next(p for t,p in calls if t == topic))
    assert original["entity_picture"] == first.picture_url
    assert "entity_picture" not in original["device"]
    calls.clear()
    publisher.sync(snapshot(first))
    assert not any(t == topic for t,p in calls)
    for picture in ("https://lh3.googleusercontent.com/synthetic-picture-b", None):
        calls.clear()
        publisher.sync(snapshot(replace(first, picture_url=picture)))
        config = json.loads(next(p for t,p in calls if t == topic))
        assert config.get("entity_picture") == picture
        assert config["unique_id"] == original["unique_id"]
        assert config["json_attributes_topic"] == original["json_attributes_topic"]
        location = json.loads(next(p for t,p in calls if t.endswith("/location")))
        assert location["latitude"] == PERSON.latitude
        assert location["source_timestamp"] == PERSON.source_timestamp
    calls.clear()
    publisher.sync(snapshot(PERSON), force=True)
    config = json.loads(next(p for t,p in calls if t == topic))
    assert "entity_picture" not in config
