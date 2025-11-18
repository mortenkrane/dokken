"""Git operations for documentation workflow."""

import subprocess
from datetime import datetime

from rich.console import Console

console = Console()

GIT_BASE_BRANCH = "main"


def setup_git() -> None:
    """
    Sets up git for documentation generation:
    1. Checks out main branch
    2. Pulls latest changes
    3. Creates a new branch with format dokken/docs-<ISO date>
    """
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
