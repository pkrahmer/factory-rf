"""The root of the errors the factory raises on purpose."""


class FactoryError(Exception):
    """Every error the factory raises on purpose."""


class BoundaryError(FactoryError):
    """An outside party failed."""


class HostingServiceError(BoundaryError):
    """A call to the hosting service failed."""

    operation: str
    detail: str

    def __init__(self, operation: str, detail: str) -> None:
        """Name the failed operation and what the hosting service reported."""
        super().__init__(f"hosting service {operation} failed: {detail}")
        self.operation = operation
        self.detail = detail
