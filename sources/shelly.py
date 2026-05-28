import asyncio
import logging
import os
from typing import Any

from fastapi import FastAPI, Request

from registry import Registry
from sources import Source

logger = logging.getLogger(__name__)

SHELLY_NAME = os.environ.get("SHELLY_NAME", "Indoor")
SHELLY_SOURCE_ID = os.environ.get("SHELLY_SOURCE_ID", "shelly.indoor")


def _to_float(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


class ShellySource(Source):
    """Receives webhooks from a Shelly H&T Gen3.

    The device is battery-powered and wakes briefly to push readings, so we
    expose an ingest endpoint instead of polling. Accepts temperature/humidity
    as query params (Shelly's URL-action style) or as a JSON body.
    """

    def __init__(self) -> None:
        self._last: dict[str, Any] = {}

    async def run(self, registry: Registry) -> None:
        # No background work; data arrives via the webhook.
        await asyncio.Event().wait()

    def register_routes(self, app: FastAPI, registry: Registry) -> None:
        @app.api_route("/api/ingest/shelly", methods=["GET", "POST"])
        async def ingest(request: Request) -> dict:
            params: dict[str, Any] = dict(request.query_params)
            if request.method == "POST":
                try:
                    body = await request.json()
                    if isinstance(body, dict):
                        params = {**params, **body}
                except Exception:
                    pass

            temp = _to_float(
                params.get("temperature")
                or params.get("temp")
                or params.get("tC")
            )
            hum = _to_float(
                params.get("humidity")
                or params.get("hum")
                or params.get("rh")
            )
            battery = _to_float(
                params.get("battery")
                or params.get("bat")
                or params.get("battery_percent")
            )

            if temp is not None:
                self._last["temperature_c"] = temp
            if hum is not None:
                self._last["humidity_pct"] = hum
            if battery is not None:
                self._last["battery_pct"] = battery
            if "device_id" in params:
                self._last["device_id"] = params["device_id"]

            registry.publish(
                SHELLY_SOURCE_ID,
                name=SHELLY_NAME,
                type="ShellyHTG3",
                data=dict(self._last),
            )
            logger.info(f"Shelly ingest: {self._last}")
            return {"ok": True}
