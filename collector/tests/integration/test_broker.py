"""Execute only against the disposable Compose broker, never a household broker."""

import os
from threading import Event
import pytest
import paho.mqtt.client as paho

pytestmark = pytest.mark.skipif(not os.environ.get("BROKER_TEST_HOST"),
    reason="requires disposable Compose test broker")


def connection(user):
    client = paho.Client(paho.CallbackAPIVersion.VERSION2, protocol=paho.MQTTv5)
    client.username_pw_set(user, "synthetic-" + user + "-password")
    connected = Event()
    client.on_connect = lambda c, u, f, code, properties: connected.set() if code == 0 else None
    client.connect(os.environ["BROKER_TEST_HOST"], 1883)
    client.loop_start()
    assert connected.wait(10)
    return client


def test_discovery_delivery_and_acl_denials():
    collector, ha = connection("collector"), connection("homeassistant")
    received, subscribed = Event(), Event()
    messages = []
    topic = "google_maps_collector/synthetic-test/availability"
    def message(c, u, msg):
        messages.append((msg.topic, msg.payload))
        if msg.topic == topic:
            received.set()
    ha.on_message = message
    ha.on_subscribe = lambda *args: subscribed.set()
    try:
        ha.subscribe(topic, qos=1)
        assert subscribed.wait(5)
        collector.publish(topic, "online", qos=1, retain=True).wait_for_publish(5)
        assert received.wait(5)
        assert (topic, b"online") in messages
        denied = Event()
        results = []
        def acknowledged(c, u, mid, reason, properties):
            results.append(reason.value)
            denied.set()
        ha.on_publish = acknowledged
        ha.publish("unrelated/private", "synthetic-denied", qos=1)
        assert denied.wait(5)
        assert results == [135]  # MQTT v5 Not authorized.
    finally:
        collector.disconnect(); collector.loop_stop()
        ha.disconnect(); ha.loop_stop()


def test_reconnect_retains_discovery_and_timestamp():
    import json
    from google_maps_collector.google_maps import Person
    from google_maps_collector.mqtt import Publisher, contact_id
    collector = connection("collector")
    def publish(topic, payload, **kw):
        collector.publish(topic, payload, **kw).wait_for_publish(5)
    person = Person("synthetic-restart", 0.5, 0.25, 25, 1800000000, 73)
    try:
        Publisher(publish).sync({"people": [person], "available": {person.id}, "status": "ready"}, force=True)
    finally:
        collector.disconnect(); collector.loop_stop()
    ha = connection("homeassistant")
    observed = Event()
    received = []
    topic = "google_maps_collector/" + contact_id(person.id) + "/location"
    def message(c, u, msg):
        received.append(json.loads(msg.payload))
        observed.set()
    ha.on_message = message
    try:
        ha.subscribe(topic, qos=1)
        assert observed.wait(5)
        assert received[0]["source_timestamp"] == person.source_timestamp
    finally:
        ha.disconnect(); ha.loop_stop()
