"""Code analysis and context extraction for documentation generation."""

import glob
import os

from rich.console import Console

console = Console()


def get_module_context(*, module_path: str) -> str:
    """
    Fetches the full code content for all Python files in a module directory.

    Args:
        module_path: The path to the module directory to analyze.

    Returns:
        A formatted string containing all Python files' content.
    """
    try:
        # Find all Python files in the module directory
        python_files = glob.glob(os.path.join(module_path, "*.py"))

        if not python_files:
            console.print(f"[yellow]⚠[/yellow] No Python files found in {module_path}")
            return ""

        context = f"--- MODULE PATH: {module_path} ---\n\n"

        for file_path in sorted(python_files):
            # Get the current file content
            with open(file_path) as f:
                code_content = f.read()

            # Add file context
            context += f"--- FILE: {file_path} ---\n{code_content}\n\n"

        return context
    except Exception as e:  # noqa: BLE001
        console.print(f"[red]Error getting module context for {module_path}:[/red] {e}")
        return ""
