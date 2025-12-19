"""Interactive questionnaire for capturing human intent in documentation."""

import questionary
from questionary import ValidationError, Validator
from rich.console import Console

from src.records import HumanIntent

console = Console()


class NonEmptyValidator(Validator):
    """Validator to ensure non-empty input."""

    def validate(self, document):
        """Validate that the document text is not empty."""
        if not document.text.strip():
            raise ValidationError(
                message="This field cannot be empty. Press Ctrl+C to skip.",
                cursor_position=len(document.text),
            )


def ask_human_intent() -> HumanIntent | None:
    """
    Run an interactive questionnaire to capture human intent for documentation.

    Users can skip any question by pressing Ctrl+C, or skip the entire questionnaire
    by pressing Ctrl+C on the first question.

    Returns:
        HumanIntent object with user responses, or None if user skipped the
        questionnaire.
    """
    console.print(
        "\n[bold cyan]Human Intent Capture[/bold cyan]\n"
        "[dim]Help us understand the intent behind your module.[/dim]\n"
        "[dim]Press Ctrl+C to skip questions, Meta+Enter or Esc+Enter to "
        "submit.[/dim]\n"
    )

    questions = [
        {
            "field": "problems_solved",
            "prompt": "What problems does this module solve?",
        },
        {
            "field": "core_responsibilities",
            "prompt": "What are the module's core responsibilities?",
        },
        {
            "field": "non_responsibilities",
            "prompt": "What is NOT this module's responsibility?",
        },
        {
            "field": "system_context",
            "prompt": "How does the module fit into the larger system?",
        },
    ]

    responses = {}
    for i, question in enumerate(questions):
        try:
            answer = questionary.text(
                f"[{i + 1}/{len(questions)}] {question['prompt']}",
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
                responses[question["field"]] = None
                continue

            # Store non-empty answers, or None for empty answers
            responses[question["field"]] = answer.strip() if answer.strip() else None

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
    return HumanIntent(**responses)
