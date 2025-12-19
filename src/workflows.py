"""High-level workflows for documentation generation and drift checking."""

import os
import sys

from llama_index.core.llms import LLM
from rich.console import Console

from src.code_analyzer import get_module_context
from src.config import _find_repo_root
from src.doc_configs import DOC_CONFIGS, DocConfig
from src.doc_types import DocType
from src.exceptions import DocumentationDriftError
from src.human_in_the_loop import ask_human_intent
from src.llm import check_drift, generate_doc, initialize_llm

console = Console()

# Constants
NO_DOC_MARKER = "No existing documentation provided."


def resolve_output_path(*, doc_type: DocType, module_path: str) -> str:
    """
    Resolve output path with explicit error handling.

    Args:
        doc_type: Type of documentation being generated.
        module_path: Path to the module directory (or any directory in the repo).

    Returns:
        Absolute path to the output documentation file.

    Raises:
        ValueError: If git root not found for repo-wide doc types.
        PermissionError: If cannot create necessary directories.
    """
    if doc_type == DocType.MODULE_README:
        return os.path.join(module_path, "README.md")

    # Find git root for repo-wide docs
    repo_root = _find_repo_root(module_path)
    if not repo_root:
        raise ValueError(
            f"Cannot generate {doc_type.value}: not in a git repository. "
            f"Initialize git or use MODULE_README type."
        )

    if doc_type == DocType.PROJECT_README:
        return os.path.join(repo_root, "README.md")

    if doc_type == DocType.STYLE_GUIDE:
        # Explicit side effect: create docs/ directory
        docs_dir = os.path.join(repo_root, "docs")
        try:
            os.makedirs(docs_dir, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(f"Cannot create {docs_dir}: {e}") from e
        return os.path.join(docs_dir, "style-guide.md")

    raise ValueError(f"Unknown doc type: {doc_type}")


def check_documentation_drift(  # noqa: C901
    *,
    target_module_path: str,
    fix: bool = False,
    depth: int | None = None,
    doc_type: DocType = DocType.MODULE_README,
) -> None:
    """
    Check mode: Analyzes documentation drift without generating new documentation.
    Raises DocumentationDriftError if drift is detected.

    Args:
        target_module_path: Path to the module directory to check.
        fix: If True, automatically fixes detected drift.
        depth: Directory depth to traverse. If None, uses doc type's default.
        doc_type: Type of documentation to check.

    Raises:
        DocumentationDriftError: If documentation drift is detected and fix=False.
        SystemExit: If the target path is invalid.
    """
    if not os.path.isdir(target_module_path):
        console.print(
            f"[red]Error:[/red] {target_module_path} is not a valid directory"
        )
        sys.exit(1)

    # Get doc type configuration
    doc_config = DOC_CONFIGS[doc_type]

    # Resolve output path based on doc type
    output_path = resolve_output_path(doc_type=doc_type, module_path=target_module_path)

    # Determine analysis path and depth
    if doc_config.analyze_entire_repo:
        repo_root = _find_repo_root(target_module_path)
        if not repo_root:
            console.print(
                f"[red]Error:[/red] Cannot check {doc_type.value}: "
                "not in a git repository"
            )
            sys.exit(1)
        analysis_path = repo_root
        analysis_depth = depth if depth is not None else doc_config.default_depth
    else:
        analysis_path = target_module_path
        analysis_depth = depth if depth is not None else doc_config.default_depth

    console.print(f"\n[dim]Doc type:[/dim] {doc_type.value}")
    console.print(f"[dim]Analysis path:[/dim] {analysis_path}")
    console.print(f"[dim]Documentation path:[/dim] {output_path}\n")

    # 1. Setup
    with console.status("[cyan]Initializing LLM..."):
        llm_client = initialize_llm()

    with console.status("[cyan]Analyzing code context..."):
        code_context = get_module_context(
            module_path=analysis_path, depth=analysis_depth
        )

    if not code_context:
        console.print(
            "[yellow]⚠[/yellow] No code context found. No drift check needed."
        )
        return

    # Check for existing documentation
    if not os.path.exists(output_path):
        console.print(
            f"[yellow]⚠[/yellow] No existing documentation found at {output_path}. "
            f"Try running `dokken generate --doc-type {doc_type.value}` first."
        )
        raise DocumentationDriftError(
            rationale="No documentation exists.",
            module_path=target_module_path,
        )

    with open(output_path) as f:
        current_doc_content = f.read()
    console.print("[green]✓[/green] Found existing documentation\n")

    # 2. Check for Documentation Drift
    with console.status("[cyan]Checking for documentation drift..."):
        drift_check = check_drift(
            llm=llm_client, context=code_context, current_doc=current_doc_content
        )

    console.print(f"[bold]Drift Detected:[/bold] {drift_check.drift_detected}")
    console.print(f"[bold]Rationale:[/bold] {drift_check.rationale}\n")

    if drift_check.drift_detected:
        if fix:
            fix_documentation_drift(
                llm_client=llm_client,
                code_context=code_context,
                output_path=output_path,
                doc_config=doc_config,
            )
            return

        raise DocumentationDriftError(
            rationale=drift_check.rationale, module_path=target_module_path
        )


def fix_documentation_drift(
    *, llm_client: LLM, code_context: str, output_path: str, doc_config: DocConfig
) -> None:
    """
    Fix documentation drift by generating and writing updated documentation.

    Args:
        llm_client: The LLM client to use for generation.
        code_context: The code context to analyze.
        output_path: Path to the documentation file to update.
        doc_config: DocConfig instance for the documentation type.
    """
    console.print("[cyan]Fixing drift by generating updated documentation...\n")

    # Capture human intent (doc-type-specific)
    human_intent = ask_human_intent(
        intent_model=doc_config.intent_model, questions=doc_config.intent_questions
    )

    with console.status("[cyan]Generating documentation..."):
        new_doc_data = generate_doc(
            llm=llm_client,
            context=code_context,
            human_intent=human_intent,
            output_model=doc_config.model,
            prompt_template=doc_config.prompt,
        )

    final_markdown = doc_config.formatter(doc_data=new_doc_data)

    with open(output_path, "w") as f:
        f.write(final_markdown)

    console.print(
        f"[green]✓[/green] Documentation updated and saved to: "
        f"[bold]{output_path}[/bold]\n"
    )


def generate_documentation(
    *,
    target_module_path: str,
    depth: int | None = None,
    doc_type: DocType = DocType.MODULE_README,
) -> str | None:
    """
    Generate mode: Creates or updates documentation by analyzing code with AI.

    Args:
        target_module_path: Path to the module directory to document.
        depth: Directory depth to traverse. If None, uses doc type's default.
               0=root only, 1=root+1 level, -1=infinite.
        doc_type: Type of documentation to generate.

    Returns:
        Generated markdown content, or None if no generation needed.

    Raises:
        SystemExit: If the target path is invalid.
        ValueError: If git root not found for repo-wide doc types.
    """
    if not os.path.isdir(target_module_path):
        console.print(
            f"[red]Error:[/red] {target_module_path} is not a valid directory"
        )
        sys.exit(1)

    # Get doc type configuration
    doc_config = DOC_CONFIGS[doc_type]

    # Resolve output path based on doc type
    output_path = resolve_output_path(doc_type=doc_type, module_path=target_module_path)

    # Determine analysis path and depth
    if doc_config.analyze_entire_repo:
        # For repo-wide docs, analyze from git root
        repo_root = _find_repo_root(target_module_path)
        if not repo_root:
            console.print(
                f"[red]Error:[/red] Cannot generate {doc_type.value}: "
                "not in a git repository"
            )
            sys.exit(1)
        analysis_path = repo_root
        analysis_depth = depth if depth is not None else doc_config.default_depth
    else:
        # For module docs, analyze the specified module
        analysis_path = target_module_path
        analysis_depth = depth if depth is not None else doc_config.default_depth

    console.print(f"\n[dim]Doc type:[/dim] {doc_type.value}")
    console.print(f"[dim]Analysis path:[/dim] {analysis_path}")
    console.print(f"[dim]Documentation output:[/dim] {output_path}\n")

    # 1. Setup
    with console.status("[cyan]Initializing LLM..."):
        llm_client = initialize_llm()

    with console.status("[cyan]Analyzing code context..."):
        code_context = get_module_context(
            module_path=analysis_path, depth=analysis_depth
        )

    if not code_context:
        console.print("[yellow]⚠[/yellow] No code context found. Exiting.")
        return None

    # Check for existing documentation
    if os.path.exists(output_path):
        with open(output_path) as f:
            current_doc_content = f.read()
        console.print("[green]✓[/green] Found existing documentation")
    else:
        current_doc_content = NO_DOC_MARKER
        console.print("[yellow]⚠[/yellow] No existing documentation found")

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

    if not drift_check.drift_detected and NO_DOC_MARKER not in current_doc_content:
        console.print(
            "[green]✓[/green] Documentation is considered up-to-date. No new file "
            "generated."
        )
        return None

    # 3. Step 2: Capture Human Intent (doc-type-specific questions)
    console.print(
        "[bold cyan]Step 2:[/bold cyan] Capturing human intent for documentation..."
    )
    human_intent = ask_human_intent(
        intent_model=doc_config.intent_model, questions=doc_config.intent_questions
    )

    # 4. Step 3: Generate New Structured Documentation (doc-type-specific)
    console.print(
        "[bold cyan]Step 3:[/bold cyan] Generating new structured documentation..."
    )
    with console.status("[cyan]Generating documentation..."):
        new_doc_data = generate_doc(
            llm=llm_client,
            context=code_context,
            human_intent=human_intent,
            output_model=doc_config.model,
            prompt_template=doc_config.prompt,
        )

    # 5. Generate Final Markdown (doc-type-specific formatter)
    final_markdown = doc_config.formatter(doc_data=new_doc_data)

    # 6. Write documentation to output path
    with open(output_path, "w") as f:
        f.write(final_markdown)

    console.print(
        f"\n[green]✓[/green] New documentation generated and saved to: "
        f"[bold]{output_path}[/bold]"
    )

    return final_markdown
