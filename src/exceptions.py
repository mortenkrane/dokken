"""Custom exceptions for Dokken."""


class DocumentationDriftError(Exception):
    """Raised when documentation drift is detected in check mode."""

    def __init__(self, rationale: str, module_path: str):
        self.rationale = rationale
        self.module_path = module_path
        super().__init__(f"Documentation drift detected in {module_path}:\n{rationale}")
