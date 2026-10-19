"""Collector command line and explicit runtime wiring."""

import argparse
import asyncio
import json
import logging
import os
from pathlib import Path
import sys

from . import __version__
from .config import Config


def environment_config():
    return Config(
        poll_seconds=int(os.environ.get("POLL_SECONDS", "60")),
        freshness_seconds=int(os.environ.get("FRESHNESS_SECONDS", "900")),
        store_file=Path(os.environ.get("STORE_FILE", "/data/session.json")),
        key_file=Path(os.environ.get("KEY_FILE", "/run/secrets/store-key")),
        admin_file=Path(os.environ.get("ADMIN_FILE", "/run/secrets/admin-verifier")),
        mqtt_password_file=Path(os.environ.get("MQTT_PASSWORD_FILE", "/run/secrets/mqtt-password")),
        mqtt_host=os.environ.get("MQTT_HOST", "broker"),
        mqtt_port=int(os.environ.get("MQTT_PORT", "1883")),
        management_bind=os.environ.get("MANAGEMENT_BIND", "127.0.0.1"),
        management_origin=os.environ.get("MANAGEMENT_ORIGIN", "http://127.0.0.1:8787"),
    )


async def run(config):
    import uvicorn
    from .google_maps import GoogleMaps
    from .mqtt import MQTT
    from .service import Service
    from .store import EncryptedStore
    from .web import create_app

    # Uvicorn must never write request exception tracebacks or access URLs.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers = [logging.NullHandler()]
        logger.propagate = False
    google = GoogleMaps()
    mqtt = None
    tasks = []
    try:
        store = EncryptedStore(config.store_file, config.key_file)
        service = Service(config, store, google)
        verifier = json.loads(config.admin_file.read_text())
        app = create_app(service, config, verifier)
        mqtt = MQTT(config)
        server = uvicorn.Server(uvicorn.Config(app,
            host=config.management_bind, port=8787, access_log=False, log_config=None,
            proxy_headers=False, server_header=False, limit_concurrency=32,
            timeout_keep_alive=5))
        mqtt.start()

        async def polling():
            while True:
                await asyncio.to_thread(service.poll)
                await asyncio.sleep(service.retry_seconds)

        async def publishing():
            while True:
                snapshot = await asyncio.to_thread(service.snapshot)
                mqtt.sync(snapshot)
                await asyncio.sleep(1)

        async def supervise(coroutine):
            try:
                await coroutine
            except Exception:
                print("collector_worker_unavailable", file=sys.stderr)
                server.should_exit = True

        tasks = [asyncio.create_task(supervise(polling())),
                 asyncio.create_task(supervise(publishing()))]
        await server.serve()
    finally:
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        if mqtt is not None:
            await asyncio.to_thread(mqtt.stop)
        if "service" in locals():
            def close_google():
                with service.lock:
                    google.close()
            await asyncio.to_thread(close_google)
        else:
            google.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Isolated Google Maps collector")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--healthcheck", action="store_true", help="check the local management listener")
    args = parser.parse_args()
    try:
        if args.healthcheck:
            from urllib.request import ProxyHandler, build_opener
            with build_opener(ProxyHandler({})).open(environment_config().management_origin + "/", timeout=3) as response:
                if response.status != 200:
                    raise ValueError()
            return
        asyncio.run(run(environment_config()))
    except KeyboardInterrupt:
        pass
    except Exception:
        print("collector_startup_or_runtime_unavailable", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
