"""High-level workflows for documentation generation and drift checking."""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from llama_index.core.llms import LLM
from rich.console import Console

from src.code_analyzer import get_module_context
from src.config import load_config
from src.doc_configs import DOC_CONFIGS, AnyDocConfig
from src.doc_types import DocType
from src.exceptions import DocumentationDriftError
from src.file_utils import ensure_output_directory, find_repo_root, resolve_output_path
from src.human_in_the_loop import ask_human_intent
from src.llm import GenerationConfig, check_drift, generate_doc, initialize_llm

console = Console()

# Constants
NO_DOC_MARKER = "No existing documentation provided."


@dataclass
class DocumentationContext:
    """Context information for documentation generation or drift checking."""

    doc_config: AnyDocConfig
    output_path: str
    analysis_path: str
    analysis_depth: int


def prepare_documentation_context(
    *,
    target_module_path: str,
    doc_type: DocType,
    depth: int | None,
) -> DocumentationContext:
    """
    Prepare context for documentation generation or drift checking.

    Args:
        target_module_path: Path to the module directory.
        doc_type: Type of documentation to process.
        depth: Directory depth to traverse, or None to use doc type's default.

    Returns:
        DocumentationContext with all necessary paths and configuration.

    Raises:
        SystemExit: If the target path is invalid or git root not found.
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
        repo_root = find_repo_root(target_module_path)
        if repo_root is None:
            console.print(
                f"[red]Error:[/red] Cannot process {doc_type.value}: "
                "not in a git repository"
            )
            sys.exit(1)
        # Type narrowing: repo_root is str here (sys.exit prevents None)
        analysis_path = cast(str, repo_root)
    else:
        analysis_path = target_module_path

    analysis_depth = depth if depth is not None else doc_config.default_depth

    # Print context information
    console.print(f"\n[dim]Doc type:[/dim] {doc_type.value}")
    console.print(f"[dim]Analysis path:[/dim] {analysis_path}")
    console.print(f"[dim]Documentation path:[/dim] {output_path}\n")

    return DocumentationContext(
        doc_config=doc_config,
        output_path=output_path,
        analysis_path=analysis_path,
        analysis_depth=analysis_depth,
    )


def _initialize_documentation_workflow(
    *,
    target_module_path: str,
    doc_type: DocType,
    depth: int | None,
) -> tuple[LLM, DocumentationContext, str]:
    """
    Common setup for documentation workflows.

    Initializes LLM, prepares documentation context, and analyzes code.

    Args:
        target_module_path: Path to the module directory.
        doc_type: Type of documentation to process.
        depth: Directory depth to traverse, or None to use doc type's default.

    Returns:
        Tuple of (llm_client, context, code_context).

    Raises:
        SystemExit: If the target path is invalid or git root not found.
    """
    # Prepare documentation context
    ctx = prepare_documentation_context(
        target_module_path=target_module_path,
        doc_type=doc_type,
        depth=depth,
    )

    # Initialize LLM
    with console.status("[cyan]Initializing LLM..."):
        llm_client = initialize_llm()

    # Analyze code context
    with console.status("[cyan]Analyzing code context..."):
        code_context = get_module_context(
            module_path=ctx.analysis_path, depth=ctx.analysis_depth
        )

    return llm_client, ctx, code_context


def check_documentation_drift(
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
    # Initialize workflow
    llm_client, ctx, code_context = _initialize_documentation_workflow(
        target_module_path=target_module_path,
        doc_type=doc_type,
        depth=depth,
    )

    if not code_context:
        console.print(
            "[yellow]⚠[/yellow] No code context found. No drift check needed."
        )
        return

    # Check for existing documentation
    if not os.path.exists(ctx.output_path):
        console.print(
            f"[yellow]⚠[/yellow] No existing documentation found at {ctx.output_path}. "
            f"Try running `dokken generate --doc-type {doc_type.value}` first."
        )
        raise DocumentationDriftError(
            rationale="No documentation exists.",
            module_path=target_module_path,
        )

    with open(ctx.output_path) as f:
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
                output_path=ctx.output_path,
                doc_config=ctx.doc_config,
                drift_rationale=drift_check.rationale,
                doc_type=doc_type,
                module_path=target_module_path,
            )
            return

        raise DocumentationDriftError(
            rationale=drift_check.rationale, module_path=target_module_path
        )


def fix_documentation_drift(
    *,
    llm_client: LLM,
    code_context: str,
    output_path: str,
    doc_config: AnyDocConfig,
    drift_rationale: str,
    doc_type: DocType,
    module_path: str,
) -> None:
    """
    Fix documentation drift by generating and writing updated documentation.

    Args:
        llm_client: The LLM client to use for generation.
        code_context: The code context to analyze.
        output_path: Path to the documentation file to update.
        doc_config: DocConfig instance for the documentation type.
        drift_rationale: Explanation of what drift was detected.
        doc_type: The type of documentation being generated.
        module_path: Path to the module for loading config.
    """
    console.print("[cyan]Fixing drift by generating updated documentation...\n")

    # Load configuration for custom prompts
    config = load_config(module_path=module_path)

    # Capture human intent (doc-type-specific)
    human_intent = ask_human_intent(
        intent_model=doc_config.intent_model, questions=doc_config.intent_questions
    )

    # Build generation configuration
    gen_config = GenerationConfig(
        custom_prompts=config.custom_prompts,
        doc_type=doc_type,
        human_intent=human_intent,
        drift_rationale=drift_rationale,
    )

    with console.status("[cyan]Generating documentation..."):
        new_doc_data = generate_doc(
            llm=llm_client,
            context=code_context,
            config=gen_config,
            output_model=doc_config.model,
            prompt_template=doc_config.prompt,
        )

    final_markdown = doc_config.formatter(doc_data=new_doc_data)

    # Ensure parent directory exists before writing
    ensure_output_directory(output_path)

    with open(output_path, "w") as f:
        f.write(final_markdown)

    console.print(
        f"[green]✓[/green] Documentation updated and saved to: "
        f"[bold]{output_path}[/bold]\n"
    )


def _check_single_module_drift(
    *,
    module_path: str,
    repo_root: str,
    fix: bool,
    depth: int | None,
    doc_type: DocType,
) -> tuple[str, str | None]:
    """
    Check drift for a single module.

    Args:
        module_path: Relative module path from repo root.
        repo_root: Root directory of the repository.
        fix: If True, automatically fixes detected drift.
        depth: Directory depth to traverse.
        doc_type: Type of documentation to check.

    Returns:
        Tuple of (module_path, error_rationale_or_None).
        - If no drift: (module_path, None)
        - If drift detected: (module_path, rationale)
        - If module doesn't exist: (module_path, None) for categorization as skipped
    """
    full_module_path = str(Path(repo_root) / module_path)

    console.print(f"[bold]Module:[/bold] {module_path}")

    # Validate module path exists
    if not os.path.isdir(full_module_path):
        console.print("  [yellow]⚠[/yellow] Skipping - directory does not exist\n")
        return module_path, None

    try:
        check_documentation_drift(
            target_module_path=full_module_path,
            fix=fix,
            depth=depth,
            doc_type=doc_type,
        )
        console.print("  [green]✓ No drift detected[/green]\n")
        return module_path, None
    except DocumentationDriftError as drift_error:
        console.print(f"  [red]✗ Drift detected:[/red] {drift_error.rationale}\n")
        return module_path, drift_error.rationale


def _print_drift_summary(
    *,
    modules_without_drift: list[str],
    modules_with_drift: list[tuple[str, str]],
    modules_skipped: list[str],
    total_modules: int,
) -> None:
    """
    Print formatted drift check summary.

    Args:
        modules_without_drift: List of module paths with no drift.
        modules_with_drift: List of (module_path, rationale) tuples for
            modules with drift.
        modules_skipped: List of module paths that were skipped.
        total_modules: Total number of modules configured.
    """
    console.print("[bold cyan]Summary:[/bold cyan]")
    console.print(f"  Total modules configured: {total_modules}")
    console.print(f"  [green]✓ Up-to-date:[/green] {len(modules_without_drift)}")
    console.print(f"  [red]✗ With drift:[/red] {len(modules_with_drift)}")
    if modules_skipped:
        console.print(f"  [yellow]⚠ Skipped:[/yellow] {len(modules_skipped)}")

    if modules_with_drift:
        console.print("\n[bold red]Modules with drift:[/bold red]")
        for module_path, _ in modules_with_drift:
            console.print(f"  • {module_path}")


def check_multiple_modules_drift(
    *,
    fix: bool = False,
    depth: int | None = None,
    doc_type: DocType = DocType.MODULE_README,
) -> None:
    """
    Check drift for all modules configured in .dokken.toml.

    Processes modules sequentially and reports drift status for each.
    Raises DocumentationDriftError if any module has drift and fix=False.

    Args:
        fix: If True, automatically fixes detected drift.
        depth: Directory depth to traverse. If None, uses doc type's default.
        doc_type: Type of documentation to check.

    Raises:
        DocumentationDriftError: If any module has drift and fix=False.
        ValueError: If no modules are configured in .dokken.toml.
    """
    # Find repo root to load config
    repo_root = find_repo_root(".")
    if repo_root is None:
        console.print(
            "[red]Error:[/red] Not in a git repository. "
            "Multi-module checking requires a git repository."
        )
        sys.exit(1)

    # Type narrowing: repo_root is guaranteed str after sys.exit check
    assert repo_root is not None

    # Load config from repo root
    config = load_config(module_path=repo_root)

    if not config.modules:
        console.print(
            "[red]Error:[/red] No modules configured in .dokken.toml. "
            "Add a [modules] section with module paths to check."
        )
        sys.exit(1)

    console.print(
        f"\n[bold cyan]Checking {len(config.modules)} modules for "
        f"drift...[/bold cyan]\n"
    )

    # Process each module and collect results
    results = [
        _check_single_module_drift(
            module_path=module_path,
            repo_root=repo_root,
            fix=fix,
            depth=depth,
            doc_type=doc_type,
        )
        for module_path in config.modules
    ]

    # Categorize results by drift status
    modules_with_drift = []
    modules_without_drift = []
    modules_skipped = []

    for module_path, rationale in results:
        full_module_path = str(Path(repo_root) / module_path)
        if not os.path.isdir(full_module_path):
            modules_skipped.append(module_path)
        elif rationale is not None:
            modules_with_drift.append((module_path, rationale))
        else:
            modules_without_drift.append(module_path)

    # Print summary
    _print_drift_summary(
        modules_without_drift=modules_without_drift,
        modules_with_drift=modules_with_drift,
        modules_skipped=modules_skipped,
        total_modules=len(config.modules),
    )

    # Raise error if drift detected in any module
    if modules_with_drift:
        rationales = "\n".join(
            f"  - {path}: {rationale}" for path, rationale in modules_with_drift
        )
        raise DocumentationDriftError(
            rationale=(
                f"{len(modules_with_drift)} module(s) have documentation "
                f"drift:\n{rationales}"
            ),
            module_path="multiple modules",
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
    # Initialize workflow
    llm_client, ctx, code_context = _initialize_documentation_workflow(
        target_module_path=target_module_path,
        doc_type=doc_type,
        depth=depth,
    )

    if not code_context:
        console.print("[yellow]⚠[/yellow] No code context found. Exiting.")
        return None

    # Check for existing documentation
    if os.path.exists(ctx.output_path):
        with open(ctx.output_path) as f:
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

    # Load configuration for custom prompts
    config = load_config(module_path=target_module_path)

    # 3. Step 2: Capture Human Intent (doc-type-specific questions)
    console.print(
        "[bold cyan]Step 2:[/bold cyan] Capturing human intent for documentation..."
    )
    human_intent = ask_human_intent(
        intent_model=ctx.doc_config.intent_model,
        questions=ctx.doc_config.intent_questions,
    )

    # Build generation configuration
    gen_config = GenerationConfig(
        custom_prompts=config.custom_prompts,
        doc_type=doc_type,
        human_intent=human_intent,
        drift_rationale=(drift_check.rationale if drift_check.drift_detected else None),
    )

    # 4. Step 3: Generate New Structured Documentation (doc-type-specific)
    console.print(
        "[bold cyan]Step 3:[/bold cyan] Generating new structured documentation..."
    )
    with console.status("[cyan]Generating documentation..."):
        new_doc_data = generate_doc(
            llm=llm_client,
            context=code_context,
            config=gen_config,
            output_model=ctx.doc_config.model,
            prompt_template=ctx.doc_config.prompt,
        )

    # 5. Generate Final Markdown (doc-type-specific formatter)
    final_markdown = ctx.doc_config.formatter(doc_data=new_doc_data)

    # 6. Write documentation to output path
    # Ensure parent directory exists before writing
    ensure_output_directory(ctx.output_path)

    with open(ctx.output_path, "w") as f:
        f.write(final_markdown)

    console.print(
        f"\n[green]✓[/green] New documentation generated and saved to: "
        f"[bold]{ctx.output_path}[/bold]"
    )

    return final_markdown
