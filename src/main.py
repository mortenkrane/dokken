"""Dokken CLI - AI-powered documentation generation and drift detection tool."""

import sys

import click
from rich.console import Console
from rich.panel import Panel

from src.doc_types import DocType
from src.exceptions import DocumentationDriftError
from src.workflows import check_documentation_drift, generate_documentation

console = Console()

# Constants for CLI options
DEPTH_HELP = "Directory depth to traverse (0=root only, 1=root+1 level, -1=infinite)"
DOC_TYPE_HELP = (
    "Type of documentation to generate: "
    "module-readme (module architectural docs), "
    "project-readme (top-level project README), "
    "style-guide (code conventions guide)"
)


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
    "module_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
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
    help=DEPTH_HELP + " (defaults to doc type's default)",
)
@click.option(
    "--doc-type",
    type=click.Choice(
        ["module-readme", "project-readme", "style-guide"], case_sensitive=False
    ),
    default="module-readme",
    help=DOC_TYPE_HELP,
)
def check(module_path: str, fix: bool, depth: int | None, doc_type: str):
    """Check for documentation drift without generating new docs.

    This command analyzes your code and documentation to detect if they're out of sync.
    If drift is detected, it exits with code 1, making it perfect for CI/CD pipelines.

    Use --fix to automatically update the documentation when drift is detected.

    Example:
        dokken check src/payment_service
        dokken check src/payment_service --fix
        dokken check src/payment_service --doc-type project-readme
        dokken check src/payment_service --depth 2
    """
    try:
        # Convert string to DocType enum
        doc_type_enum = DocType(doc_type)

        console.print(
            Panel.fit(
                "[bold blue]Documentation Drift Check[/bold blue]",
                subtitle=f"Module: {module_path} | Type: {doc_type}",
            )
        )
        check_documentation_drift(
            target_module_path=module_path, fix=fix, depth=depth, doc_type=doc_type_enum
        )
        console.print("\n[bold green]✓ Documentation is up-to-date![/bold green]")
    except DocumentationDriftError as drift_error:
        console.print(f"\n[bold red]✗ {drift_error}[/bold red]")
        sys.exit(1)
    except ValueError as config_error:
        console.print(f"[bold red]Configuration Error:[/bold red] {config_error}")
        sys.exit(1)


@cli.command()
@click.argument(
    "module_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option(
    "--depth",
    type=click.IntRange(min=-1),
    default=None,
    help=DEPTH_HELP + " (defaults to doc type's default)",
)
@click.option(
    "--doc-type",
    type=click.Choice(
        ["module-readme", "project-readme", "style-guide"], case_sensitive=False
    ),
    default="module-readme",
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


if __name__ == "__main__":
    cli()
