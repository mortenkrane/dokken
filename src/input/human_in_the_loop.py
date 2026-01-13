"""Interactive questionnaire for capturing human intent in documentation."""

import questionary
from pydantic import BaseModel
from rich.console import Console

from src.doctypes import DOC_CONFIGS, DocType

console = Console()


def ask_human_intent(
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

    console.print(
        "\n[bold cyan]Human Intent Capture[/bold cyan]\n"
        "[dim]Help us understand the intent behind the code you need to "
        "document.[/dim]\n"
        "[dim]Press Ctrl+C to skip questions, Meta+Enter or Esc+Enter to "
        "submit.[/dim]\n"
    )

    responses = {}
    for i, question_config in enumerate(questions):
        try:
            answer = questionary.text(
                f"[{i + 1}/{len(questions)}] {question_config['question']}",
                multiline=True,
                instruction="(Ctrl+C to skip, Meta+Enter or Esc+Enter to submit)",
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
