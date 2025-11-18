"""High-level workflows for documentation generation and drift checking."""

import os
import sys

from rich.console import Console

from src.code_analyzer import get_module_context
from src.exceptions import DocumentationDriftError
from src.formatters import generate_markdown
from src.git import GIT_BASE_BRANCH, setup_git
from src.llm import check_drift, generate_doc, initialize_llm

console = Console()


def check_documentation_drift(*, target_module_path: str) -> None:
    """
    Check mode: Analyzes documentation drift without generating new documentation.
    Raises DocumentationDriftError if drift is detected.

    Args:
        target_module_path: Path to the module directory to check.

    Raises:
        DocumentationDriftError: If documentation drift is detected.
        SystemExit: If the target path is invalid.
    """
    if not os.path.isdir(target_module_path):
        console.print(
            f"[red]Error:[/red] {target_module_path} is not a valid directory"
        )
        sys.exit(1)

    readme_path = os.path.join(target_module_path, "README.md")

    console.print(f"\n[dim]Target module:[/dim] {target_module_path}")
    console.print(f"[dim]Documentation path:[/dim] {readme_path}\n")

    # 1. Setup
    with console.status("[cyan]Initializing LLM..."):
        llm_client = initialize_llm()

    with console.status("[cyan]Analyzing code context..."):
        code_context = get_module_context(
            module_path=target_module_path, base_branch=GIT_BASE_BRANCH
        )

    if not code_context:
        console.print(
            "[yellow]⚠[/yellow] No code context found. No drift check needed."
        )
        return

    # Check for existing README.md
    if not os.path.exists(readme_path):
        console.print(
            f"[yellow]⚠[/yellow] No existing README.md found at {readme_path}"
        )
        raise DocumentationDriftError(
            rationale="No documentation exists for this module.",
            module_path=target_module_path,
        )

    with open(readme_path) as f:
        current_doc_content = f.read()
    console.print("[green]✓[/green] Found existing README.md\n")

    # 2. Check for Documentation Drift
    with console.status("[cyan]Checking for documentation drift..."):
        drift_check = check_drift(
            llm=llm_client, context=code_context, current_doc=current_doc_content
        )

    console.print(f"[bold]Drift Detected:[/bold] {drift_check.drift_detected}")
    console.print(f"[bold]Rationale:[/bold] {drift_check.rationale}\n")

    if drift_check.drift_detected:
        raise DocumentationDriftError(
            rationale=drift_check.rationale, module_path=target_module_path
        )


def generate_documentation(*, target_module_path: str) -> str | None:
    """
    Generate mode: Creates or updates documentation by analyzing code with AI.

    Args:
        target_module_path: Path to the module directory to document.

    Raises:
        SystemExit: If the target path is invalid.
    """
    if not os.path.isdir(target_module_path):
        console.print(
            f"[red]Error:[/red] {target_module_path} is not a valid directory"
        )
        sys.exit(1)

    # Documentation will be written to README.md in the target module
    readme_path = os.path.join(target_module_path, "README.md")

    console.print(f"\n[dim]Target module:[/dim] {target_module_path}")
    console.print(f"[dim]Documentation output:[/dim] {readme_path}\n")

    # 0. Git setup
    setup_git()

    # 1. Setup
    with console.status("[cyan]Initializing LLM..."):
        llm_client = initialize_llm()

    with console.status("[cyan]Analyzing code context..."):
        code_context = get_module_context(
            module_path=target_module_path, base_branch=GIT_BASE_BRANCH
        )

    if not code_context:
        console.print("[yellow]⚠[/yellow] No code context found. Exiting.")
        return None

    # Check for existing README.md
    if os.path.exists(readme_path):
        with open(readme_path) as f:
            current_doc_content = f.read()
        console.print("[green]✓[/green] Found existing README.md")
    else:
        current_doc_content = "No existing documentation provided."
        console.print("[yellow]⚠[/yellow] No existing README.md found")

    # 2. Step 1: Check for Documentation Drift
    console.print(
        "\n[bold cyan]Step 1:[/bold cyan] Checking for documentation drift..."
    )
    with console.status("[cyan]Analyzing drift..."):
        drift_check = check_drift(
            llm=llm_client, context=code_context, current_doc=current_doc_content
        )

    console.print(f"[bold]Drift Detected:[/bold] {drift_check.drift_detected}")
    console.print(f"[bold]Rationale:[/bold] {drift_check.rationale}\n")

    if (
        not drift_check.drift_detected
        and "No existing documentation provided." not in current_doc_content
    ):
        console.print(
            "[green]✓[/green] Documentation is considered up-to-date. No new file generated."
        )
        return None

    # 3. Step 2: Generate New Structured Documentation
    console.print(
        "[bold cyan]Step 2:[/bold cyan] Generating new structured documentation..."
    )
    with console.status("[cyan]Generating documentation..."):
        new_doc_data = generate_doc(llm=llm_client, context=code_context)

    # 4. Generate Final Markdown (Stabilization)
    final_markdown = generate_markdown(doc_data=new_doc_data)

    # 5. Overwrite README.md with the new documentation
    with open(readme_path, "w") as f:
        f.write(final_markdown)

    console.print(
        f"\n[green]✓[/green] New documentation generated and saved to: [bold]{readme_path}[/bold]"
    )

    return final_markdown
