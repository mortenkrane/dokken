"""Dokken CLI - AI-powered documentation generation and drift detection tool."""

import sys

import click
from rich.console import Console
from rich.panel import Panel

from src.cache import (
    load_drift_cache_from_disk,
    save_drift_cache_to_disk,
    set_cache_max_size,
)
from src.config import load_config
from src.constants import DEFAULT_CACHE_FILE
from src.doctypes import DocType
from src.exceptions import DocumentationDriftError
from src.file_utils import find_repo_root
from src.workflows import (
    check_documentation_drift,
    check_multiple_modules_drift,
    generate_documentation,
)

console = Console()

# Constants for CLI options
DEPTH_HELP = (
    "Directory depth to traverse (0=root only, 1=root+1 level, -1=infinite). "
    "Defaults: module-readme=0, project-readme=1, style-guide=-1"
)

# Doc type descriptions for help text
DOC_TYPE_DESCRIPTIONS = {
    DocType.MODULE_README: "module architectural docs",
    DocType.PROJECT_README: "top-level project README",
    DocType.STYLE_GUIDE: "code conventions guide",
}

# Build help text dynamically from enum
DOC_TYPE_HELP = "Type of documentation to generate: " + ", ".join(
    f"{dt.value} ({DOC_TYPE_DESCRIPTIONS[dt]})" for dt in DocType
)


# --- Helper Functions ---


def _get_cache_file_path(module_path: str) -> str:
    """
    Get the cache file path from config and apply cache settings.

    Also sets the cache max size from configuration.

    Args:
        module_path: Path to the module being processed.

    Returns:
        Path to the cache file.
    """
    try:
        config = load_config(module_path=module_path)
        # Apply cache configuration
        set_cache_max_size(config.cache.max_size)
        return config.cache.file
    except (ValueError, OSError, RuntimeError):
        # If config loading fails, use default
        return DEFAULT_CACHE_FILE


def _validate_check_args(module_path: str | None, check_all: bool) -> None:
    """
    Validate arguments for the check command.

    Args:
        module_path: Optional module path.
        check_all: Whether to check all modules.

    Raises:
        SystemExit: If arguments are invalid.
    """
    if check_all and module_path:
        console.print(
            "[bold red]Error:[/bold red] Cannot use --all with a module path. "
            "Use either --all or specify a module path."
        )
        sys.exit(1)

    if not check_all and not module_path:
        console.print(
            "[bold red]Error:[/bold red] Must specify either a module "
            "path or --all flag."
        )
        sys.exit(1)


def _get_cache_module_path(module_path: str | None, check_all: bool) -> str:
    """
    Determine the module path to use for cache file lookup.

    Args:
        module_path: The provided module path, or None.
        check_all: Whether checking all modules.

    Returns:
        The module path to use for cache configuration lookup.
    """
    if module_path:
        return module_path

    # For --all without module_path, try to use repo root
    if check_all:
        repo_root = find_repo_root(".")
        if repo_root:
            return repo_root

    return "."


# --- CLI Interface ---


@click.group()
@click.version_option(version="0.1.0", prog_name="dokken")
def cli():
    """Dokken - AI-powered documentation generation and drift detection tool.

    Dokken helps you keep your documentation in sync with your code by detecting
    drift and generating up-to-date documentation automatically.
    """


@cli.command()
@click.argument(
    "module_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=False,
)
@click.option(
    "--all",
    "check_all",
    is_flag=True,
    help="Check all modules configured in .dokken.toml",
)
@click.option(
    "--fix",
    is_flag=True,
    help="Automatically fix detected drift by updating the documentation",
)
@click.option(
    "--depth",
    type=click.IntRange(min=-1),
    default=None,
    help=DEPTH_HELP,
)
@click.option(
    "--doc-type",
    type=click.Choice([dt.value for dt in DocType], case_sensitive=False),
    default=DocType.MODULE_README.value,
    help=DOC_TYPE_HELP,
)
def check(
    module_path: str | None,
    check_all: bool,
    fix: bool,
    depth: int | None,
    doc_type: str,
):
    """Check for documentation drift without generating new docs.

    This command analyzes your code and documentation to detect if they're out of sync.
    If drift is detected, it exits with code 1, making it perfect for CI/CD pipelines.

    Use --fix to automatically update the documentation when drift is detected.

    Use --all to check all modules configured in .dokken.toml.

    Example:
        dokken check src/payment_service
        dokken check src/payment_service --fix
        dokken check --all
        dokken check --all --fix
        dokken check src/payment_service --doc-type project-readme
        dokken check src/payment_service --depth 2
    """
    # Validate arguments
    _validate_check_args(module_path, check_all)

    # Determine module path for cache loading
    cache_module_path = _get_cache_module_path(module_path, check_all)

    # Load persistent cache
    cache_file = _get_cache_file_path(cache_module_path)
    load_drift_cache_from_disk(cache_file)

    try:
        # Convert string to DocType enum
        doc_type_enum = DocType(doc_type)

        if check_all:
            # Check all modules from config
            console.print(
                Panel.fit(
                    "[bold blue]Multi-Module Documentation Drift Check[/bold blue]",
                    subtitle=f"Type: {doc_type}",
                )
            )
            check_multiple_modules_drift(fix=fix, depth=depth, doc_type=doc_type_enum)
            console.print("\n[bold green]✓ All modules are up-to-date![/bold green]")
        else:
            # Check single module - module_path guaranteed non-None by validation
            assert module_path is not None  # Type narrowing
            console.print(
                Panel.fit(
                    "[bold blue]Documentation Drift Check[/bold blue]",
                    subtitle=f"Module: {module_path} | Type: {doc_type}",
                )
            )
            check_documentation_drift(
                target_module_path=module_path,
                fix=fix,
                depth=depth,
                doc_type=doc_type_enum,
            )
            console.print("\n[bold green]✓ Documentation is up-to-date![/bold green]")
    except DocumentationDriftError as drift_error:
        console.print(f"\n[bold red]✗ {drift_error}[/bold red]")
        sys.exit(1)
    except ValueError as config_error:
        console.print(f"[bold red]Configuration Error:[/bold red] {config_error}")
        sys.exit(1)
    finally:
        # Always save cache, even on errors (preserves partial results)
        save_drift_cache_to_disk(cache_file)


@cli.command()
@click.argument(
    "module_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option(
    "--depth",
    type=click.IntRange(min=-1),
    default=None,
    help=DEPTH_HELP,
)
@click.option(
    "--doc-type",
    type=click.Choice([dt.value for dt in DocType], case_sensitive=False),
    default=DocType.MODULE_README.value,
    help=DOC_TYPE_HELP,
)
def generate(module_path: str, depth: int | None, doc_type: str):
    """Generate fresh documentation for a module or project.

    This command creates or updates documentation by analyzing your code with AI.

    Example:
        dokken generate src/payment_service
        dokken generate . --doc-type project-readme
        dokken generate . --doc-type style-guide
        dokken generate src/payment_service --depth -1
    """
    # Load persistent cache
    cache_file = _get_cache_file_path(module_path)
    load_drift_cache_from_disk(cache_file)

    try:
        # Convert string to DocType enum
        doc_type_enum = DocType(doc_type)

        console.print(
            Panel.fit(
                "[bold blue]Documentation Generation[/bold blue]",
                subtitle=f"Module: {module_path} | Type: {doc_type}",
            )
        )
        final_markdown = generate_documentation(
            target_module_path=module_path, depth=depth, doc_type=doc_type_enum
        )

        if final_markdown:
            console.print(
                Panel.fit(
                    final_markdown,
                    title="[bold]Generated Documentation[/bold]",
                    border_style="green",
                )
            )

        console.print(
            "\n[bold green]✓ Documentation generated successfully![/bold green]"
        )
    except DocumentationDriftError as drift_error:
        console.print(f"\n[bold red]✗ {drift_error}[/bold red]")
        sys.exit(1)
    except ValueError as config_error:
        console.print(f"[bold red]Configuration Error:[/bold red] {config_error}")
        sys.exit(1)
    finally:
        # Always save cache, even on errors (preserves partial results)
        save_drift_cache_to_disk(cache_file)


if __name__ == "__main__":
    cli()
