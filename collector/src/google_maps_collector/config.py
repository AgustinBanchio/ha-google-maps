"""Validated settings. Credentials are referenced only through assigned files."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Config:
    poll_seconds: int = 60
    freshness_seconds: int = 900
    upload_bytes: int = 1_048_576
    store_file: Path = field(default=Path("/data/session.json"), repr=False)
    key_file: Path = field(default=Path("/run/secrets/store-key"), repr=False)
    admin_file: Path = field(default=Path("/run/secrets/admin-verifier"), repr=False)
    mqtt_password_file: Path = field(default=Path("/run/secrets/mqtt-password"), repr=False)
    mqtt_host: str = "broker"
    mqtt_port: int = 1883
    mqtt_username: str = "collector"
    management_bind: str = "127.0.0.1"
    management_origin: str = "http://127.0.0.1:8787"

    def __post_init__(self) -> None:
        from urllib.parse import urlsplit

        for value, low, high in (
            (self.poll_seconds, 15, 3600),
            (self.freshness_seconds, 300, 3600),
            (self.upload_bytes, 1, 1_048_576),
            (self.mqtt_port, 1, 65535),
        ):
            if type(value) is not int or not low <= value <= high:
                raise ValueError("configuration value outside allowed bounds")
        if self.management_bind not in {"127.0.0.1", "0.0.0.0"}:
            raise ValueError("invalid management bind address")
        origin = urlsplit(self.management_origin)
        if (origin.scheme != "http" or origin.hostname not in {"127.0.0.1", "localhost"}
                or origin.username or origin.password or origin.path or origin.query
                or origin.fragment or origin.port != 8787):
            raise ValueError("management origin must be loopback HTTP on port 8787")
