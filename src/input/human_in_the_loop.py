"""Interactive questionnaire for capturing human intent in documentation."""

import questionary
from pydantic import BaseModel
from rich.console import Console

from src.doctypes import DOC_CONFIGS, DocType

console = Console()


def display_question_preview(questions: list[dict[str, str]]) -> bool:
    """
    Display a preview of all questions before asking them.

    Shows users what questions they'll be asked and allows them to continue or skip.

    Args:
        questions: List of dicts with 'key' and 'question' fields.

    Returns:
        True if user wants to continue, False if they want to skip.
    """
    console.print(
        f"\n[bold cyan]Question Preview[/bold cyan]\n"
        f"[dim]You will be asked {len(questions)} question(s) about the code "
        f"you need to document.[/dim]\n"
    )

    for i, question_config in enumerate(questions, start=1):
        console.print(f"[cyan]{i}.[/cyan] {question_config['question']}")

    console.print(
        "\n[dim]Press Enter to continue or Ctrl+C to skip the questionnaire.[/dim]"
    )

    try:
        input()
        return True
    except KeyboardInterrupt:
        console.print(
            "\n[yellow]Questionnaire skipped. "
            "Continuing without human intent.[/yellow]\n"
        )
        return False


def ask_human_intent(  # noqa: C901
    *,
    intent_model: type[BaseModel],
    questions: list[dict[str, str]] | None = None,
) -> BaseModel | None:
    """
    Run an interactive questionnaire to capture human intent for documentation.

    Users can skip any question by pressing Ctrl+C, or skip the entire questionnaire
    by pressing Ctrl+C on the first question.

    Args:
        intent_model: The Pydantic model to use for intent (e.g., ModuleIntent,
                      ProjectIntent, StyleGuideIntent).
        questions: List of dicts with 'key' and 'question' fields. If None, uses
                   default module questions.

    Returns:
        Intent model instance with user responses, or None if user skipped the
        questionnaire.
    """
    if questions is None:
        # Use module questions as default (most common case)
        questions = DOC_CONFIGS[DocType.MODULE_README].intent_questions

    # Show question preview first
    if not display_question_preview(questions):
        return None

    console.print(
        "\n[bold cyan]Human Intent Capture[/bold cyan]\n"
        "[dim]Help us understand the intent behind the code you need to "
        "document.[/dim]\n"
        "[dim]Your answers can span multiple lines - press Enter for new lines "
        "within your answer.[/dim]\n"
        "[dim]To submit: Use Esc+Enter or Ctrl+D (reliable). Meta+Enter may work "
        "depending on your terminal.[/dim]\n"
        "[dim]Press Ctrl+C to skip any question.[/dim]\n"
    )

    responses = {}
    for i, question_config in enumerate(questions):
        try:
            # Display question on separate line with rich formatting
            console.print(
                f"\n[bold cyan][{i + 1}/{len(questions)}][/bold cyan] "
                f"{question_config['question']}\n"
            )

            # Then prompt for answer
            answer = questionary.text(
                "Answer:",
                multiline=True,
                instruction="(Ctrl+C to skip, Esc+Enter or Ctrl+D to submit)",
            ).ask()

            # If user pressed Ctrl+C on first question, skip entire questionnaire
            if answer is None and i == 0:
                console.print(
                    "\n[yellow]Questionnaire skipped. "
                    "Continuing without human intent.[/yellow]\n"
                )
                return None

            # If user pressed Ctrl+C on any other question, just skip that question
            if answer is None:
                responses[question_config["key"]] = None
                continue

            # Store non-empty answers, or None for empty answers
            responses[question_config["key"]] = (
                answer.strip() if answer.strip() else None
            )

        except KeyboardInterrupt:
            console.print(
                "\n[yellow]Questionnaire interrupted. "
                "Continuing without human intent.[/yellow]\n"
            )
            return None

    # Check if user provided any responses
    if not any(responses.values()):
        console.print(
            "\n[yellow]No responses provided. "
            "Continuing without human intent.[/yellow]\n"
        )
        return None

    console.print("\n[green]✓[/green] Human intent captured successfully!\n")
    return intent_model(**responses)
