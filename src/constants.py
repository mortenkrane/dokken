"""Shared constants and error messages for Dokken."""

# Special markers
NO_DOC_MARKER = "No existing documentation provided."

# Error messages
ERROR_NOT_IN_GIT_REPO = "not in a git repository"
ERROR_NOT_IN_GIT_REPO_MULTI_MODULE = (
    "Not in a git repository. Multi-module checking requires a git repository."
)
ERROR_INVALID_DIRECTORY = "{path} is not a valid directory"
ERROR_NO_MODULES_CONFIGURED = (
    "No modules configured in .dokken.toml. "
    "Add a [modules] section with module paths to check."
)
ERROR_CANNOT_CREATE_DIR = "Cannot create {parent_dir}: {error}"
ERROR_NO_API_KEY = (
    "No API key found. Please set one of the following environment variables:\n"
    "  - ANTHROPIC_API_KEY (for Claude)\n"
    "  - OPENAI_API_KEY (for OpenAI)\n"
    "  - GOOGLE_API_KEY (for Google Gemini)"
)

# Cache configuration
DRIFT_CACHE_SIZE = 100
