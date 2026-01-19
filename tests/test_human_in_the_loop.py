"""Tests for the human-in-the-loop questionnaire functionality."""

from unittest.mock import patch

from src.input.human_in_the_loop import (
    _collect_answers,
    ask_human_intent,
    confirm_or_edit_answers,
    display_answer_summary,
    display_question_preview,
)
from src.records import ModuleIntent


def test_ask_human_intent_full_responses():
    """Test questionnaire with full responses for all questions."""
    with (
        patch("src.input.human_in_the_loop.display_question_preview") as mock_preview,
        patch("src.input.human_in_the_loop._collect_answers") as mock_collect,
        patch("src.input.human_in_the_loop.confirm_or_edit_answers") as mock_confirm,
        patch("src.input.human_in_the_loop.console.print"),
    ):
        mock_preview.return_value = True
        responses = {
            "problems_solved": "Handles payment processing",
            "core_responsibilities": "Payment gateway integration",
            "non_responsibilities": "Tax calculation",
            "system_context": "Part of e-commerce system",
        }
        mock_collect.return_value = responses
        mock_confirm.return_value = (True, responses, set())

        result = ask_human_intent(intent_model=ModuleIntent)

        assert result is not None
        assert isinstance(result, ModuleIntent)
        assert result.problems_solved == "Handles payment processing"
        assert result.core_responsibilities == "Payment gateway integration"
        assert result.non_responsibilities == "Tax calculation"
        assert result.system_context == "Part of e-commerce system"
        assert mock_preview.called


def test_ask_human_intent_skip_first_question():
    """Test that pressing ESC on first question skips entire questionnaire."""
    with (
        patch("src.input.human_in_the_loop.questionary.text") as mock_text,
        patch("src.input.human_in_the_loop.display_question_preview") as mock_preview,
        patch("src.input.human_in_the_loop.console.print"),
    ):
        mock_preview.return_value = True
        # Return None (ESC pressed) on first question
        mock_text.return_value.ask.return_value = None

        result = ask_human_intent(intent_model=ModuleIntent)

        assert result is None
        # Should only call once (first question)
        assert mock_text.return_value.ask.call_count == 1


def test_ask_human_intent_skip_later_questions():
    """Test that pressing ESC on later questions skips those questions."""
    with (
        patch("src.input.human_in_the_loop.display_question_preview") as mock_preview,
        patch("src.input.human_in_the_loop._collect_answers") as mock_collect,
        patch("src.input.human_in_the_loop.confirm_or_edit_answers") as mock_confirm,
        patch("src.input.human_in_the_loop.console.print"),
    ):
        mock_preview.return_value = True
        # Answer first two, skip last two
        responses = {
            "problems_solved": "Handles authentication",
            "core_responsibilities": "User login and registration",
            "non_responsibilities": None,
            "system_context": None,
        }
        mock_collect.return_value = responses
        mock_confirm.return_value = (True, responses, set())

        result = ask_human_intent(intent_model=ModuleIntent)

        assert result is not None
        assert isinstance(result, ModuleIntent)
        assert result.problems_solved == "Handles authentication"
        assert result.core_responsibilities == "User login and registration"
        assert result.non_responsibilities is None
        assert result.system_context is None


def test_ask_human_intent_empty_responses():
    """Test that empty string responses are converted to None."""
    with (
        patch("src.input.human_in_the_loop.display_question_preview") as mock_preview,
        patch("src.input.human_in_the_loop._collect_answers") as mock_collect,
        patch("src.input.human_in_the_loop.confirm_or_edit_answers") as mock_confirm,
        patch("src.input.human_in_the_loop.console.print"),
    ):
        mock_preview.return_value = True
        responses = {
            "problems_solved": "Has a value",
            "core_responsibilities": None,
            "non_responsibilities": None,
            "system_context": "Another value",
        }
        mock_collect.return_value = responses
        mock_confirm.return_value = (True, responses, set())

        result = ask_human_intent(intent_model=ModuleIntent)

        assert result is not None
        assert isinstance(result, ModuleIntent)
        assert result.problems_solved == "Has a value"
        assert result.core_responsibilities is None
        assert result.non_responsibilities is None
        assert result.system_context == "Another value"


def test_ask_human_intent_all_empty_responses():
    """Test that all empty responses returns None."""
    with (
        patch("src.input.human_in_the_loop.display_question_preview") as mock_preview,
        patch("src.input.human_in_the_loop._collect_answers") as mock_collect,
        patch("src.input.human_in_the_loop.confirm_or_edit_answers") as mock_confirm,
        patch("src.input.human_in_the_loop.console.print"),
    ):
        mock_preview.return_value = True
        # Return all empty/None responses
        responses = {
            "problems_solved": None,
            "core_responsibilities": None,
            "non_responsibilities": None,
            "system_context": None,
        }
        mock_collect.return_value = responses
        mock_confirm.return_value = (True, responses, set())

        result = ask_human_intent(intent_model=ModuleIntent)

        assert result is None


def test_ask_human_intent_keyboard_interrupt():
    """Test that keyboard interrupt returns None."""
    with (
        patch("src.input.human_in_the_loop.questionary.text") as mock_text,
        patch("src.input.human_in_the_loop.display_question_preview") as mock_preview,
        patch("src.input.human_in_the_loop.console.print"),
    ):
        mock_preview.return_value = True
        # Raise KeyboardInterrupt on first question
        mock_text.return_value.ask.side_effect = KeyboardInterrupt()

        result = ask_human_intent(intent_model=ModuleIntent)

        assert result is None


def test_ask_human_intent_skip_at_preview():
    """Test that skipping at the preview screen returns None."""
    with (
        patch("src.input.human_in_the_loop.questionary.text") as mock_text,
        patch("src.input.human_in_the_loop.display_question_preview") as mock_preview,
        patch("src.input.human_in_the_loop.console.print"),
    ):
        # User skips at preview
        mock_preview.return_value = False

        result = ask_human_intent(intent_model=ModuleIntent)

        assert result is None
        # Should not ask any questions if preview was skipped
        assert mock_text.return_value.ask.call_count == 0


def test_display_question_preview_continue():
    """Test that display_question_preview returns True when user continues."""
    questions = [
        {"key": "q1", "question": "What does this do?"},
        {"key": "q2", "question": "What are its responsibilities?"},
    ]

    with (
        patch("src.input.human_in_the_loop.console.print") as mock_print,
        patch("builtins.input") as mock_input,
    ):
        # User presses Enter to continue
        mock_input.return_value = ""

        result = display_question_preview(questions)

        assert result is True
        # Verify console.print was called with preview content
        assert mock_print.call_count >= 3  # Header, questions, footer


def test_display_question_preview_skip():
    """Test that display_question_preview returns False when user skips."""
    questions = [
        {"key": "q1", "question": "What does this do?"},
        {"key": "q2", "question": "What are its responsibilities?"},
    ]

    with (
        patch("src.input.human_in_the_loop.console.print") as mock_print,
        patch("builtins.input") as mock_input,
    ):
        # User presses Ctrl+C to skip
        mock_input.side_effect = KeyboardInterrupt()

        result = display_question_preview(questions)

        assert result is False
        # Verify skip message was printed
        assert mock_print.call_count >= 3  # Header, questions, skip message


def test_display_answer_summary():
    """Test that display_answer_summary shows answers correctly."""
    questions = [
        {"key": "q1", "question": "What does this do?"},
        {"key": "q2", "question": "What are its responsibilities?"},
        {"key": "q3", "question": "What is it not responsible for?"},
    ]
    responses = {
        "q1": "Handles payment processing",
        "q2": None,  # Skipped
        "q3": "Tax calculation",
    }
    edited_keys = {"q3"}

    with patch("src.input.human_in_the_loop.console.print") as mock_print:
        display_answer_summary(responses, questions, edited_keys)

        # Verify console.print was called (summary table displayed)
        assert mock_print.called


def test_confirm_or_edit_answers_confirm():
    """Test that confirm_or_edit_answers allows confirming answers."""
    questions = [
        {"key": "q1", "question": "What does this do?"},
        {"key": "q2", "question": "What are its responsibilities?"},
    ]
    responses = {
        "q1": "Handles authentication",
        "q2": "User login and registration",
    }
    edited_keys: set[str] = set()

    with (
        patch("src.input.human_in_the_loop.display_answer_summary") as mock_summary,
        patch("src.input.human_in_the_loop.questionary.select") as mock_select,
    ):
        # User chooses to confirm
        mock_select.return_value.ask.return_value = "✓ Confirm and continue"

        confirmed, result_responses, result_edited = confirm_or_edit_answers(
            responses, questions, edited_keys
        )

        assert confirmed is True
        assert result_responses == responses
        assert result_edited == edited_keys
        assert mock_summary.called


def test_confirm_or_edit_answers_cancel():
    """Test that confirm_or_edit_answers allows cancelling."""
    questions = [
        {"key": "q1", "question": "What does this do?"},
    ]
    responses = {"q1": "Test"}
    edited_keys: set[str] = set()

    with (
        patch("src.input.human_in_the_loop.display_answer_summary"),
        patch("src.input.human_in_the_loop.questionary.select") as mock_select,
    ):
        # User chooses to cancel
        mock_select.return_value.ask.return_value = "⊗ Cancel questionnaire"

        confirmed, result_responses, result_edited = confirm_or_edit_answers(
            responses, questions, edited_keys
        )

        assert confirmed is False
        assert result_responses is None  # None for cancel
        assert result_edited is None


def test_confirm_or_edit_answers_start_over():
    """Test that confirm_or_edit_answers allows starting over."""
    questions = [
        {"key": "q1", "question": "What does this do?"},
    ]
    responses = {"q1": "Test"}
    edited_keys: set[str] = set()

    with (
        patch("src.input.human_in_the_loop.display_answer_summary"),
        patch("src.input.human_in_the_loop.questionary.select") as mock_select,
    ):
        # User chooses to start over
        mock_select.return_value.ask.return_value = "↻ Start over"

        confirmed, result_responses, result_edited = confirm_or_edit_answers(
            responses, questions, edited_keys
        )

        assert confirmed is False
        assert result_responses == {}
        assert result_edited == set()


def test_confirm_or_edit_answers_edit():
    """Test that confirm_or_edit_answers allows editing an answer."""
    questions = [
        {"key": "q1", "question": "What does this do?"},
        {"key": "q2", "question": "What are its responsibilities?"},
    ]
    responses = {
        "q1": "Old answer",
        "q2": "Responsibilities",
    }
    edited_keys: set[str] = set()

    with (
        patch("src.input.human_in_the_loop.display_answer_summary"),
        patch("src.input.human_in_the_loop.questionary.select") as mock_select,
        patch("src.input.human_in_the_loop.questionary.text") as mock_text,
        patch("src.input.human_in_the_loop.console.print"),
    ):
        # User chooses to edit, then selects first question, then confirms
        mock_select.return_value.ask.side_effect = [
            "✎ Edit an answer",  # First menu choice
            "1. What does this do?",  # Select first question
            "✓ Confirm and continue",  # Confirm after editing
        ]
        # New answer for the edited question
        mock_text.return_value.ask.return_value = "New answer"

        confirmed, result_responses, result_edited = confirm_or_edit_answers(
            responses, questions, edited_keys
        )

        assert confirmed is True
        assert result_responses["q1"] == "New answer"
        assert result_responses["q2"] == "Responsibilities"
        assert "q1" in result_edited


def test_confirm_or_edit_answers_edit_back():
    """Test that user can go back from edit menu."""
    questions = [
        {"key": "q1", "question": "What does this do?"},
    ]
    responses = {"q1": "Test"}
    edited_keys: set[str] = set()

    with (
        patch("src.input.human_in_the_loop.display_answer_summary"),
        patch("src.input.human_in_the_loop.questionary.select") as mock_select,
    ):
        # User chooses to edit, then goes back, then confirms
        mock_select.return_value.ask.side_effect = [
            "✎ Edit an answer",  # First menu choice
            "← Back to summary",  # Go back
            "✓ Confirm and continue",  # Confirm
        ]

        confirmed, result_responses, result_edited = confirm_or_edit_answers(
            responses, questions, edited_keys
        )

        assert confirmed is True
        assert result_responses == responses
        assert result_edited == edited_keys


def test_ask_human_intent_with_confirmation():
    """Test questionnaire with confirmation flow."""
    with (
        patch("src.input.human_in_the_loop.display_question_preview") as mock_preview,
        patch("src.input.human_in_the_loop._collect_answers") as mock_collect,
        patch("src.input.human_in_the_loop.confirm_or_edit_answers") as mock_confirm,
        patch("src.input.human_in_the_loop.console.print"),
    ):
        mock_preview.return_value = True
        mock_collect.return_value = {
            "problems_solved": "Payment processing",
            "core_responsibilities": "Gateway integration",
            "non_responsibilities": None,
            "system_context": "E-commerce",
        }
        # User confirms on first try
        mock_confirm.return_value = (
            True,
            mock_collect.return_value,
            set(),
        )

        result = ask_human_intent(intent_model=ModuleIntent)

        assert result is not None
        assert isinstance(result, ModuleIntent)
        assert result.problems_solved == "Payment processing"
        assert mock_confirm.called


def test_ask_human_intent_with_restart():
    """Test questionnaire with restart flow."""
    with (
        patch("src.input.human_in_the_loop.display_question_preview") as mock_preview,
        patch("src.input.human_in_the_loop._collect_answers") as mock_collect,
        patch("src.input.human_in_the_loop.confirm_or_edit_answers") as mock_confirm,
        patch("src.input.human_in_the_loop.console.print"),
    ):
        mock_preview.return_value = True

        # First attempt responses
        first_responses = {
            "problems_solved": "First answer",
            "core_responsibilities": "First responsibility",
            "non_responsibilities": None,
            "system_context": None,
        }

        # Second attempt responses
        second_responses = {
            "problems_solved": "Better answer",
            "core_responsibilities": "Better responsibility",
            "non_responsibilities": None,
            "system_context": "Better context",
        }

        # User restarts, then confirms on second try
        mock_collect.side_effect = [first_responses, second_responses]
        mock_confirm.side_effect = [
            (False, {}, set()),  # Restart
            (True, second_responses, set()),  # Confirm
        ]

        result = ask_human_intent(intent_model=ModuleIntent)

        assert result is not None
        assert isinstance(result, ModuleIntent)
        assert result.problems_solved == "Better answer"
        assert mock_collect.call_count == 2
        assert mock_confirm.call_count == 2


def test_ask_human_intent_with_cancel_at_confirmation():
    """Test that cancelling at confirmation screen returns None."""
    with (
        patch("src.input.human_in_the_loop.display_question_preview") as mock_preview,
        patch("src.input.human_in_the_loop._collect_answers") as mock_collect,
        patch("src.input.human_in_the_loop.confirm_or_edit_answers") as mock_confirm,
        patch("src.input.human_in_the_loop.console.print"),
    ):
        mock_preview.return_value = True
        mock_collect.return_value = {
            "problems_solved": "Test",
            "core_responsibilities": "Test",
            "non_responsibilities": None,
            "system_context": None,
        }
        # User cancels at confirmation
        mock_confirm.return_value = (False, None, None)

        result = ask_human_intent(intent_model=ModuleIntent)

        assert result is None


def test_confirm_or_edit_answers_edit_skipped_answer():
    """Test editing an answer that was previously skipped."""
    questions = [
        {"key": "q1", "question": "What does this do?"},
        {"key": "q2", "question": "What are its responsibilities?"},
    ]
    responses = {
        "q1": "Has answer",
        "q2": None,  # Previously skipped
    }
    edited_keys: set[str] = set()

    with (
        patch("src.input.human_in_the_loop.display_answer_summary"),
        patch("src.input.human_in_the_loop.questionary.select") as mock_select,
        patch("src.input.human_in_the_loop.questionary.text") as mock_text,
        patch("src.input.human_in_the_loop.console.print"),
    ):
        # User chooses to edit skipped question, then confirms
        mock_select.return_value.ask.side_effect = [
            "✎ Edit an answer",  # First menu choice
            "2. What are its responsibilities?",  # Select second (skipped) question
            "✓ Confirm and continue",  # Confirm after editing
        ]
        # New answer for the previously skipped question
        mock_text.return_value.ask.return_value = "New responsibility"

        confirmed, result_responses, result_edited = confirm_or_edit_answers(
            responses, questions, edited_keys
        )

        assert confirmed is True
        assert result_responses["q2"] == "New responsibility"
        assert "q2" in result_edited


def test_confirm_or_edit_answers_cancel_during_edit():
    """Test cancelling (Ctrl+C) while editing an answer."""
    questions = [
        {"key": "q1", "question": "What does this do?"},
    ]
    responses = {"q1": "Original answer"}
    edited_keys: set[str] = set()

    with (
        patch("src.input.human_in_the_loop.display_answer_summary"),
        patch("src.input.human_in_the_loop.questionary.select") as mock_select,
        patch("src.input.human_in_the_loop.questionary.text") as mock_text,
        patch("src.input.human_in_the_loop.console.print"),
    ):
        # User chooses to edit, starts editing, then cancels, then confirms
        mock_select.return_value.ask.side_effect = [
            "✎ Edit an answer",  # Choose to edit
            "1. What does this do?",  # Select question
            "✓ Confirm and continue",  # Confirm after cancelling edit
        ]
        # User presses Ctrl+C while editing (returns None)
        mock_text.return_value.ask.return_value = None

        confirmed, result_responses, result_edited = confirm_or_edit_answers(
            responses, questions, edited_keys
        )

        # Answer should remain unchanged
        assert confirmed is True
        assert result_responses["q1"] == "Original answer"
        assert "q1" not in result_edited


def test_collect_answers_skip_later_question():
    """Test _collect_answers when user skips a later question with Ctrl+C."""
    questions = [
        {"key": "q1", "question": "First question?"},
        {"key": "q2", "question": "Second question?"},
        {"key": "q3", "question": "Third question?"},
    ]

    with (
        patch("src.input.human_in_the_loop.questionary.text") as mock_text,
        patch("src.input.human_in_the_loop.console.print"),
    ):
        # Answer first, skip second (None), answer third
        mock_text.return_value.ask.side_effect = [
            "First answer",
            None,  # Skip second question
            "Third answer",
        ]

        result = _collect_answers(questions)

        assert result is not None
        assert result["q1"] == "First answer"
        assert result["q2"] is None  # Skipped
        assert result["q3"] == "Third answer"
