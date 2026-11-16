"""Validation diagnostics for the ratified mathematical FIR contracts."""


class FIRValidationError(ValueError):
    """One primary diagnostic with an envelope-relative JSON Pointer."""

    def __init__(self, category: str, path: str, message: str) -> None:
        self.category = category
        self.path = path
        super().__init__(f"{category} at {path or '/'}: {message}")
