"""One-time local provisioning; no secret values are printed or accepted as arguments."""

import argparse
import base64
import getpass
import hashlib
import json
import os
from pathlib import Path
import secrets
import tempfile

from google_maps_collector.web import password_verifier


FILES = ("store-key", "admin-verifier", "mqtt-password", "ha-password", "broker-passwords")


def broker_hash(password):
    # Mosquitto's documented/source PBKDF2-SHA512 ($7$) password-file format.
    salt = secrets.token_bytes(12)
    iterations = 210_000
    digest = hashlib.pbkdf2_hmac("sha512", password.encode(), salt, iterations)
    return "$7${}${}${}".format(iterations, base64.b64encode(salt).decode(),
                                 base64.b64encode(digest).decode())


def bootstrap(directory: Path, password: str, *, assign_ownership=True):
    directory = directory.absolute()
    if directory.is_symlink():
        raise ValueError("bootstrap directory must not be a symlink")
    if directory.exists():
        if ((directory / "bootstrap-complete").is_file()
                and all((directory / name).is_file() for name in FILES)
                and all((directory / name).is_dir() for name in ("data", "broker-data"))):
            return False  # Never regenerate files or keys on repeated bootstrap.
        raise ValueError("partial bootstrap; restore the complete original directory")
    if not directory.parent.is_dir():
        raise ValueError("create the private parent directory first")
    verifier = password_verifier(password)
    mqtt_password, ha_password = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    content = {"store-key": secrets.token_bytes(32),
        "admin-verifier": json.dumps(verifier).encode(),
        "mqtt-password": mqtt_password.encode(), "ha-password": ha_password.encode(),
        "broker-passwords": (f"collector:{broker_hash(mqtt_password)}\n"
                             f"homeassistant:{broker_hash(ha_password)}\n").encode()}
    staging = Path(tempfile.mkdtemp(prefix=".bootstrap-", dir=directory.parent))
    try:
        for name, data in content.items():
            path = staging / name
            with path.open("xb") as output:
                os.chmod(path, 0o400)
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
        for name in ("data", "broker-data"):
            (staging / name).mkdir(mode=0o700)
        (staging / "bootstrap-complete").write_text("1\n")
        os.chmod(staging, 0o711)
        if os.name == "posix" and assign_ownership:
            # File-backed Compose secrets preserve host ownership, not secrets.uid.
            if os.geteuid() != 0:
                raise ValueError("Linux bootstrap requires root for assigned file ownership")
            for name in ("store-key", "admin-verifier", "mqtt-password", "data"):
                os.chown(staging / name, 10001, 10001)
            for name in ("broker-passwords", "broker-data"):
                os.chown(staging / name, 1883, 1883)
        os.rename(staging, directory)
        if os.name == "posix":
            descriptor = os.open(directory.parent, os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        return True
    finally:
        if staging.exists():
            # Only remove files created in this known staging directory, never recurse.
            for child in staging.iterdir():
                if child.is_dir():
                    child.rmdir()
                else:
                    os.chmod(child, 0o600)
                    child.unlink()
            staging.rmdir()


def main():
    parser = argparse.ArgumentParser(description="Provision private collector files once")
    parser.add_argument("--directory", type=Path, default=Path(".local/collector"))
    args = parser.parse_args()
    if args.directory.exists():
        password = ""  # A repeat must not ask for or replace the old password.
    else:
        password = getpass.getpass("New collector admin password (12+ characters): ")
        if password != getpass.getpass("Repeat collector admin password: "):
            parser.error("passwords differ")
    try:
        created = bootstrap(args.directory, password)
        print("bootstrap_created" if created else "bootstrap_already_exists")
    except (ValueError, OSError):
        parser.exit(1, "bootstrap_unavailable; inspect private directory permissions and completeness\n")


if __name__ == "__main__":
    main()
