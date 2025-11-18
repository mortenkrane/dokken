import glob
import os
import subprocess
import sys

import click
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.llms.google_genai import GoogleGenAI
from rich.console import Console
from rich.panel import Panel

from src.records import ComponentDocumentation, DocumentationDriftCheck

console = Console()

GIT_BASE_BRANCH = "main"


class DocumentationDriftError(Exception):
    """Raised when documentation drift is detected in check mode."""

    def __init__(self, rationale: str, module_path: str):
        self.rationale = rationale
        self.module_path = module_path
        super().__init__(f"Documentation drift detected in {module_path}:\n{rationale}")


def setup_git() -> None:
    """
    Sets up git for documentation generation:
    1. Checks out main branch
    2. Pulls latest changes
    3. Creates a new branch with format dokken/docs-<ISO date>
    """
    from datetime import datetime

    console.print("\n[bold cyan]Git Setup[/bold cyan]")

    # 1. Checkout main
    with console.status("[cyan]Checking out main branch..."):
        subprocess.run(
            ["git", "checkout", GIT_BASE_BRANCH],
            check=True,
            capture_output=True,
        )
    console.print("[green]✓[/green] Checked out main branch")

    # 2. Pull latest changes
    with console.status("[cyan]Pulling latest changes..."):
        subprocess.run(["git", "pull"], check=True, capture_output=True)
    console.print("[green]✓[/green] Pulled latest changes")

    # 3. Create new branch with ISO date format
    iso_date = datetime.now().strftime("%Y-%m-%d")
    branch_name = f"dokken/docs-{iso_date}"
    with console.status(f"[cyan]Creating branch {branch_name}..."):
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            check=True,
            capture_output=True,
        )
    console.print(
        f"[green]✓[/green] Created and checked out branch: [bold]{branch_name}[/bold]"
    )


def initialize_llm() -> GoogleGenAI:
    """Initializes the GoogleGenAI LLM client."""
    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY environment variable not set.")

    # Using Gemini-2.5-Flash as it has a good balance of speed, cost, and context window
    # Low temp for stability
    return GoogleGenAI(model="gemini-2.5-flash", temperature=0.0)


def get_module_context(*, module_path: str, base_branch: str = "main") -> str:
    """
    Fetches the full code content and the diff for all Python files in a module directory.

    Args:
        module_path: The path to the module directory to analyze.
        base_branch: The branch to diff against (e.g., 'main' or 'HEAD~1').

    Returns:
        A formatted string containing all Python files' content and diffs.
    """
    try:
        # Find all Python files in the module directory
        python_files = glob.glob(os.path.join(module_path, "*.py"))

        if not python_files:
            console.print(f"[yellow]⚠[/yellow] No Python files found in {module_path}")
            return ""

        context = f"--- MODULE PATH: {module_path} ---\n\n"

        for file_path in sorted(python_files):
            # 1. Get the current file content
            with open(file_path) as f:
                code_content = f.read()

            # 2. Get the diff relative to the base branch
            result = subprocess.run(
                ["git", "diff", f"{base_branch}", "--", file_path],
                capture_output=True,
                text=True,
                check=True,
            )
            diff_content = result.stdout

            # Add file context
            context += (
                f"--- FILE: {file_path} ---\n"
                f"--- CURRENT CODE CONTENT ---\n{code_content}\n"
                f"--- CODE CHANGES (GIT DIFF vs. {base_branch}) ---\n{diff_content}\n\n"
            )

        return context
    except Exception as e:
        console.print(f"[red]Error getting module context for {module_path}:[/red] {e}")
        return ""


def check_drift(
    *, llm: GoogleGenAI, context: str, current_doc: str
) -> DocumentationDriftCheck:
    """
    STEP 1: Ask the LLM to validate the current documentation against the code changes.
    """
    # Use LLMTextCompletionProgram for structured Pydantic output
    check_program = LLMTextCompletionProgram.from_defaults(
        output_cls=DocumentationDriftCheck,
        llm=llm,
        prompt_template_str=(
            "You are a Documentation Drift Detector. Your task is to analyze the "
            "provided code context and the current documentation to determine if the "
            "documentation is now obsolete, inaccurate, or missing crucial information "
            "due to the code changes. Focus specifically on high-level structure, "
            "purpose, and design decisions. "
            "--- CODE CONTEXT & DIFF ---\n{context}\n"
            "--- CURRENT DOCUMENTATION ---\n{current_doc}\n"
            "Respond ONLY with the JSON object schema provided."
        ),
    )

    # Run the check
    check_result = check_program(context=context, current_doc=current_doc)
    return check_result


def generate_doc(*, llm: GoogleGenAI, context: str) -> ComponentDocumentation:
    """
    STEP 2: Generate the complete, new structured documentation for the component.
    """
    # Use LLMTextCompletionProgram for structured Pydantic output
    generate_program = LLMTextCompletionProgram.from_defaults(
        output_cls=ComponentDocumentation,
        llm=llm,
        prompt_template_str=(
            "You are an expert technical writer. Based on the provided code context, "
            "generate a complete, structured documentation overview. "
            "Focus on the component's main purpose, scope, and the 'why' behind its design. "
            "Do not include simple function signature details (assume those are in docstrings). "
            "--- CODE CONTEXT ---\n{context}\n"
            "Respond ONLY with the JSON object schema provided."
        ),
    )

    # Run the generation
    doc_result = generate_program(context=context)
    return doc_result


def generate_markdown(*, doc_data: ComponentDocumentation) -> str:
    """
    Converts the structured Pydantic data into a human-readable Markdown string.

    NOTE: This templating step is CRITICAL for output stability!
    """
    md = f"# {doc_data.component_name} Overview\n\n"
    md += f"## Purpose & Scope\n\n{doc_data.purpose_and_scope}\n\n"

    if doc_data.external_dependencies:
        md += f"## External Dependencies\n\n{doc_data.external_dependencies}\n\n"

    md += "## Key Design Decisions (The 'Why')\n\n"

    # Sort keys for deterministic output to prevent diff noise
    sorted_decisions = sorted(doc_data.design_decisions.items())

    for key, decision_text in sorted_decisions:
        md += f"### Decision: {key}\n\n"
        md += f"{decision_text}\n\n"

    return md


def check_documentation_drift(*, target_module_path: str) -> None:
    """
    Check mode: Analyzes documentation drift without generating new documentation.
    Raises DocumentationDriftError if drift is detected.
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


def generate_documentation(*, target_module_path: str) -> None:
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
        return

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
        return

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
    console.print(
        Panel.fit(
            final_markdown,
            title="[bold]Generated Documentation[/bold]",
            border_style="green",
        )
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
        generate_documentation(target_module_path=module_path)
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
