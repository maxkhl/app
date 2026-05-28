from abc import ABC, abstractmethod

from fastapi import FastAPI

from registry import Registry


class Source(ABC):
    """A data source that publishes its latest snapshot into the registry."""

    @abstractmethod
    async def run(self, registry: Registry) -> None:
        """Start the source. Should run until cancelled."""

    def register_routes(self, app: FastAPI, registry: Registry) -> None:
        """Optional: mount inbound HTTP routes (for webhook-style sources)."""
        return
