"""Interactive questionnaire for capturing human intent in documentation."""

import questionary
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

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


def display_answer_summary(
    responses: dict[str, str | None],
    questions: list[dict[str, str]],
    edited_keys: set[str],
) -> None:
    """
    Display a formatted summary of all collected answers.

    Args:
        responses: Dictionary of question keys to answers.
        questions: List of question configurations.
        edited_keys: Set of question keys that have been edited.
    """
    table = Table(
        title="Answer Summary",
        show_header=True,
        header_style="bold cyan",
        show_lines=True,
    )
    table.add_column("Question", style="cyan", no_wrap=False)
    table.add_column("Answer", style="green", no_wrap=False)
    table.add_column("Status", style="dim", width=10)

    for question_config in questions:
        key = question_config["key"]
        answer = responses.get(key)
        question_text = question_config["question"]

        # Determine answer display and status
        if answer is None or answer == "":
            answer_display = "[dim italic](skipped)[/dim italic]"
            status = ""
        else:
            # Truncate long answers for display
            answer_display = answer if len(answer) <= 100 else f"{answer[:97]}..."
            status = "[yellow]✎ edited[/yellow]" if key in edited_keys else ""

        table.add_row(question_text, answer_display, status)

    console.print("\n")
    console.print(table)
    console.print()


def confirm_or_edit_answers(  # noqa: C901
    responses: dict[str, str | None],
    questions: list[dict[str, str]],
    edited_keys: set[str],
) -> tuple[bool, dict[str, str | None], set[str]]:
    """
    Show answer summary and ask user if they want to confirm, edit, or restart.

    Args:
        responses: Dictionary of question keys to answers.
        questions: List of question configurations.
        edited_keys: Set of question keys that have been edited.

    Returns:
        Tuple of (confirmed, responses, edited_keys).
        confirmed=True means user wants to continue with current answers.
        If confirmed=False and responses is empty, user wants to restart.
    """
    while True:
        # Display current answers
        display_answer_summary(responses, questions, edited_keys)

        # Ask what to do next
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "✓ Confirm and continue",
                "✎ Edit an answer",
                "↻ Start over",
                "⊗ Cancel questionnaire",
            ],
            instruction="(Use arrow keys)",
        ).ask()

        if choice is None or choice == "⊗ Cancel questionnaire":
            # User pressed Ctrl+C or chose to cancel
            # Use None to distinguish from restart which uses empty dict
            return (False, None, None)  # type: ignore[return-value]

        if choice == "✓ Confirm and continue":
            return (True, responses, edited_keys)

        if choice == "↻ Start over":
            # Clear all responses and signal restart
            return (False, {}, set())

        if choice == "✎ Edit an answer":
            # Let user select which question to edit
            question_choices = [
                f"{i + 1}. {q['question']}" for i, q in enumerate(questions)
            ]
            question_choices.append("← Back to summary")

            selected = questionary.select(
                "Which question do you want to edit?",
                choices=question_choices,
                instruction="(Use arrow keys)",
            ).ask()

            if selected is None or selected == "← Back to summary":
                continue  # Go back to summary

            # Extract question index
            question_idx = question_choices.index(selected)
            question_config = questions[question_idx]
            key = question_config["key"]
            current_answer = responses.get(key)

            # Show current answer
            console.print(
                f"\n[bold cyan]Question:[/bold cyan] {question_config['question']}\n"
            )
            if current_answer:
                console.print(f"[dim]Current answer:[/dim] {current_answer}\n")
            else:
                console.print("[dim]Current answer: (skipped)[/dim]\n")

            # Ask for new answer
            new_answer = questionary.text(
                "New answer:",
                default=current_answer or "",
                multiline=True,
                instruction="(Ctrl+C to cancel, Esc+Enter or Ctrl+D to submit)",
            ).ask()

            if new_answer is None:
                # User cancelled, go back to summary
                continue

            # Update the response
            responses[key] = new_answer.strip() if new_answer.strip() else None
            edited_keys.add(key)

            console.print("[green]✓[/green] Answer updated!\n")
            # Loop back to show updated summary


def _collect_answers(
    questions: list[dict[str, str]],
) -> dict[str, str | None] | None:
    """
    Collect answers to all questions in the questionnaire.

    Args:
        questions: List of question configurations.

    Returns:
        Dictionary of responses, or None if user cancelled on first question.
    """
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

    return responses


def ask_human_intent(  # noqa: C901
    *,
    intent_model: type[BaseModel],
    questions: list[dict[str, str]] | None = None,
) -> BaseModel | None:
    """
    Run an interactive questionnaire to capture human intent for documentation.

    Users can skip any question by pressing Ctrl+C, or skip the entire questionnaire
    by pressing Ctrl+C on the first question. After answering all questions, users
    can review their answers, edit them, restart, or confirm.

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

    # Main loop to allow restarting
    while True:
        # Collect answers
        responses = _collect_answers(questions)

        # If user cancelled, return None
        if responses is None:
            return None

        # Track which answers have been edited
        edited_keys: set[str] = set()

        # Show summary and allow editing
        confirmed, responses, edited_keys = confirm_or_edit_answers(
            responses, questions, edited_keys
        )

        if not confirmed:
            # Check if user wants to restart or cancel
            if responses is None:  # None means user cancelled
                console.print(
                    "\n[yellow]Questionnaire cancelled. "
                    "Continuing without human intent.[/yellow]\n"
                )
                return None
            # Empty dict (not None) means restart
            console.print("\n[cyan]Restarting questionnaire...[/cyan]\n")
            continue
        # User confirmed, check if they provided any responses
        if not any(responses.values()):
            console.print(
                "\n[yellow]No responses provided. "
                "Continuing without human intent.[/yellow]\n"
            )
            return None

        console.print("\n[green]✓[/green] Human intent captured successfully!\n")
        return intent_model(**responses)
