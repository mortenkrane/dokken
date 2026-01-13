"""Shared constants and error messages for Dokken."""

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
DEFAULT_CACHE_FILE = ".dokken-cache.json"

# LLM configuration
LLM_TEMPERATURE = 0.0  # Temperature setting for deterministic, reproducible output

# Analysis depth defaults
DEFAULT_DEPTH_MODULE = 0  # Module README: analyze only root level
DEFAULT_DEPTH_PROJECT = 1  # Project README: analyze root + 1 level
DEFAULT_DEPTH_STYLE_GUIDE = -1  # Style Guide: full recursion

# Formatter section headers - Module documentation
SECTION_MAIN_ENTRY_POINTS = "## Main Entry Points"
SECTION_PURPOSE_SCOPE = "## Purpose & Scope"
SECTION_MODULE_STRUCTURE = "## Module Structure"
SECTION_ARCHITECTURE_OVERVIEW = "## Architecture Overview"
SECTION_CONTROL_FLOW = "## Control Flow"
SECTION_EXTERNAL_DEPENDENCIES = "## External Dependencies"
SECTION_KEY_DESIGN_DECISIONS = "## Key Design Decisions"

# Formatter section headers - Project documentation
SECTION_USAGE = "## Usage"
SECTION_INSTALLATION = "## Installation"
SECTION_KEY_FEATURES = "## Key Features"
SECTION_PURPOSE = "## Purpose"
SECTION_PROJECT_STRUCTURE = "## Project Structure"
SECTION_DEVELOPMENT = "## Development"
SECTION_CONTRIBUTING = "## Contributing"

# Formatter section headers - Style guide documentation
SECTION_LANGUAGES_TOOLS = "## Languages & Tools"
SECTION_CODE_STYLE = "## Code Style"
SECTION_TESTING_CONVENTIONS = "## Testing Conventions"
SECTION_ARCHITECTURE_PATTERNS = "## Architecture & Patterns"
SECTION_MODULE_ORGANIZATION = "## Module Organization"
SECTION_GIT_WORKFLOW = "## Git Workflow"
SECTION_DEPENDENCIES = "## Dependencies"
