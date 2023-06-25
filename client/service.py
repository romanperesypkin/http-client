"""Service module."""


class Service:
    """Base class for service.

    Service is smth which can be started and stopped.
    """

    async def start(self) -> None:
        """Start service."""
        pass

    async def stop(self) -> None:
        """Stop service."""
        pass
