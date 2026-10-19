"""Explicit MQTT output schemas and a single permitted birth subscription."""

import hashlib
import json
from datetime import datetime, UTC
from threading import Event
import paho.mqtt.client as paho

PREFIX = "google_maps_collector"
GLOBAL = f"{PREFIX}/availability"
BIRTH = "homeassistant/status"


def contact_id(identity: str) -> str:
    return hashlib.sha256(identity.encode()).hexdigest()[:32]


class BrokerUnavailable(Exception):
    pass


class Publisher:
    def __init__(self, publish):
        self.publish = publish
        self.locations = {}
        self.batteries = {}
        self.availability = {}
        self.discovered = set()
        self.names = {}
        self.details = {}
        self.session = None

    def send(self, topic, payload):
        encoded = json.dumps(payload, allow_nan=False, separators=(",", ":")) if isinstance(payload, dict) else payload
        self.publish(topic, encoded, qos=1, retain=True)

    def sync(self, snapshot, force=False):
        self.send("homeassistant/binary_sensor/google_maps_collector/session/config", {
            "name": "Maps session", "unique_id": f"{PREFIX}_session",
            "state_topic": f"{PREFIX}/session", "payload_on": "ON", "payload_off": "OFF",
            "device_class": "connectivity", "availability_topic": GLOBAL,
            "entity_category": "diagnostic"}) if force or self.session is None else None
        for person in snapshot["people"]:
            key = contact_id(person.id)
            base = f"{PREFIX}/{key}"
            available = "online" if person.id in snapshot["available"] else "offline"
            availability = [{"topic": GLOBAL}, {"topic": f"{base}/availability"}]
            device_name = f"Google Maps {person.display_name}" if person.display_name else f"Maps {key[:8]}"
            common = {"availability": availability, "availability_mode": "all",
                "enabled_by_default": True, "device": {"identifiers": [f"{PREFIX}_{key}"],
                "name": device_name}}
            if key not in self.discovered or self.names.get(key) != device_name or force:
                self.send(f"homeassistant/device_tracker/{PREFIX}/{key}/config", {
                    **common, "name": "Maps location", "unique_id": f"{PREFIX}_{key}",
                    "source_type": "gps", "visible_by_default": True,
                    "json_attributes_topic": f"{base}/location"})
                self.send(f"homeassistant/sensor/{PREFIX}/{key}-battery/config", {
                    **common, "name": "Maps battery", "unique_id": f"{PREFIX}_{key}_battery",
                    "state_topic": f"{base}/battery", "device_class": "battery",
                    "unit_of_measurement": "%", "state_class": "measurement"})
                self.send(f"homeassistant/sensor/{PREFIX}/{key}-details/config", {
                    **common, "name": "Maps details", "unique_id": f"{PREFIX}_{key}_details",
                    "state_topic": f"{base}/details", "value_template": "{{ value_json.last_seen }}",
                    "device_class": "timestamp", "json_attributes_topic": f"{base}/details"})
                self.discovered.add(key)
                self.names[key] = device_name
            if self.availability.get(key) != available or force:
                # Publish unavailability before replaying any location on resync.
                if available == "offline":
                    self.send(f"{base}/availability", available)
            details = {"full_name": person.display_name, "nickname": person.nickname,
                "entity_picture": person.picture_url, "address": person.address,
                "country_code": person.country_code, "battery_level": person.battery,
                "battery_charging": person.battery_charging,
                "last_seen": datetime.fromtimestamp(person.source_timestamp, UTC).isoformat()}
            if self.details.get(key) != details or force:
                self.send(f"{base}/details", details)
                self.details[key] = details
            if (self.locations.get(key, -1) < person.source_timestamp or force) and available == "online":
                self.send(f"{base}/location", {**details, "latitude": person.latitude,
                    "longitude": person.longitude, "gps_accuracy": person.gps_accuracy,
                    "source_timestamp": person.source_timestamp})
                self.locations[key] = person.source_timestamp
            if key not in self.batteries or self.batteries[key] != person.battery or force:
                self.send(f"{base}/battery", "None" if person.battery is None else str(person.battery))
                self.batteries[key] = person.battery
            if self.availability.get(key) != available or force:
                if available == "online":
                    self.send(f"{base}/availability", available)
                self.availability[key] = available
        state = "ON" if snapshot.get("session_valid", snapshot["status"] not in
            {"credential_required", "starting", "storage_error"}) and snapshot["status"] != "storage_error" else "OFF"
        if state != self.session or force:
            self.send(f"{PREFIX}/session", state)
            self.session = state
        self.send(GLOBAL, "online")


class MQTT:
    def __init__(self, config):
        self.resync = Event()
        self.connected = Event()
        self.client = paho.Client(paho.CallbackAPIVersion.VERSION2,
            client_id="google-maps-collector", protocol=paho.MQTTv311)
        self.client.max_queued_messages_set(256)
        self.client.will_set(GLOBAL, "offline", qos=1, retain=True)
        self.client.username_pw_set(config.mqtt_username, config.mqtt_password_file.read_text().strip())
        self.client.reconnect_delay_set(min_delay=1, max_delay=60)
        self.client.on_connect = self._connected
        self.client.on_disconnect = self._disconnected
        self.client.on_message = self._message
        self.config = config
        self.publisher = Publisher(self._publish)

    def _connected(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            client.publish(GLOBAL, "offline", qos=1, retain=True)
            client.subscribe(BIRTH, qos=1)
            self.resync.set()
            self.connected.set()

    def _disconnected(self, *args):
        self.connected.clear()

    def _message(self, client, userdata, message):
        if message.topic == BIRTH and message.payload == b"online":
            self.resync.set()

    def _publish(self, topic, payload, qos, retain):
        result = self.client.publish(topic, payload, qos=qos, retain=retain)
        if result.rc != paho.MQTT_ERR_SUCCESS:
            raise BrokerUnavailable()

    def start(self):
        self.client.connect_async(self.config.mqtt_host, self.config.mqtt_port, keepalive=30)
        self.client.loop_start()

    def sync(self, snapshot):
        if self.connected.is_set():
            force = self.resync.is_set()
            self.resync.clear()
            try:
                self.publisher.sync(snapshot, force)
            except BrokerUnavailable:
                self.resync.set()

    def stop(self):
        if self.connected.is_set():
            try:
                self.client.publish(GLOBAL, "offline", qos=1, retain=True).wait_for_publish(timeout=2)
            except (RuntimeError, ValueError):
                pass
        self.client.disconnect()
        self.client.loop_stop()
