"""Dokken CLI - AI-powered documentation generation and drift detection tool."""

import sys

import click
from rich.console import Console
from rich.panel import Panel

from src.exceptions import DocumentationDriftError
from src.workflows import check_documentation_drift, generate_documentation

console = Console()


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
def check(module_path: str):
    """Check for documentation drift without generating new docs.

    This command analyzes your code and documentation to detect if they're out of sync.
    If drift is detected, it exits with code 1, making it perfect for CI/CD pipelines.

    Example:
        dokken check src/payment_service
    """
    try:
        console.print(
            Panel.fit(
                "[bold blue]Documentation Drift Check[/bold blue]",
                subtitle=f"Module: {module_path}",
            )
        )
        check_documentation_drift(target_module_path=module_path)
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
def generate(module_path: str):
    """Generate fresh documentation for a module.

    This command creates or updates documentation by analyzing your code with AI.
    It performs git setup, creates a new branch, and generates a README.md file.

    Example:
        dokken generate src/payment_service
    """
    try:
        console.print(
            Panel.fit(
                "[bold blue]Documentation Generation[/bold blue]",
                subtitle=f"Module: {module_path}",
            )
        )
        final_markdown = generate_documentation(target_module_path=module_path)

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
