"""Code analysis and context extraction for documentation generation."""

import glob
import os
import subprocess

from rich.console import Console

console = Console()


def get_module_context(*, module_path: str, base_branch: str = "main") -> str:
    """
    Fetches the full code content and the diff for all Python files in a module
    directory.

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
    except Exception as e:  # noqa: BLE001
        console.print(f"[red]Error getting module context for {module_path}:[/red] {e}")
        return ""
