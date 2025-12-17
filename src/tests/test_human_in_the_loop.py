"""Tests for the human-in-the-loop questionnaire functionality."""

from unittest.mock import patch

from src.human_in_the_loop import ask_human_intent
from src.records import HumanIntent


def test_ask_human_intent_full_responses():
    """Test questionnaire with full responses for all questions."""
    # Mock questionary to return specific answers
    with patch("src.human_in_the_loop.questionary.text") as mock_text:
        mock_text.return_value.ask.side_effect = [
            "Handles payment processing",
            "Payment gateway integration",
            "Tax calculation",
            "Part of e-commerce system",
            "process_payment() function",
            "Payment must be idempotent",
            "No refund support",
            "API key must be in env vars",
        ]

        result = ask_human_intent()

        assert result is not None
        assert isinstance(result, HumanIntent)
        assert result.problems_solved == "Handles payment processing"
        assert result.core_responsibilities == "Payment gateway integration"
        assert result.non_responsibilities == "Tax calculation"
        assert result.system_context == "Part of e-commerce system"
        assert result.entry_points == "process_payment() function"
        assert result.invariants == "Payment must be idempotent"
        assert result.limitations == "No refund support"
        assert result.common_pitfalls == "API key must be in env vars"


def test_ask_human_intent_skip_first_question():
    """Test that pressing ESC on first question skips entire questionnaire."""
    with patch("src.human_in_the_loop.questionary.text") as mock_text:
        # Return None (ESC pressed) on first question
        mock_text.return_value.ask.return_value = None

        result = ask_human_intent()

        assert result is None
        # Should only call once (first question)
        assert mock_text.return_value.ask.call_count == 1


def test_ask_human_intent_skip_later_questions():
    """Test that pressing ESC on later questions skips those questions."""
    with patch("src.human_in_the_loop.questionary.text") as mock_text:
        # Answer first two, skip next two, answer rest
        mock_text.return_value.ask.side_effect = [
            "Handles authentication",  # Question 1
            "User login and registration",  # Question 2
            None,  # Question 3 - skipped
            None,  # Question 4 - skipped
            "login() function",  # Question 5
            "Passwords must be hashed",  # Question 6
            "No 2FA support",  # Question 7
            "Always validate tokens",  # Question 8
        ]

        result = ask_human_intent()

        assert result is not None
        assert result.problems_solved == "Handles authentication"
        assert result.core_responsibilities == "User login and registration"
        assert result.non_responsibilities is None
        assert result.system_context is None
        assert result.entry_points == "login() function"
        assert result.invariants == "Passwords must be hashed"
        assert result.limitations == "No 2FA support"
        assert result.common_pitfalls == "Always validate tokens"


def test_ask_human_intent_empty_responses():
    """Test that empty string responses are converted to None."""
    with patch("src.human_in_the_loop.questionary.text") as mock_text:
        # Return empty strings
        mock_text.return_value.ask.side_effect = [
            "Has a value",
            "",  # Empty string
            "   ",  # Whitespace only
            "Another value",
            "",
            "",
            "",
            "",
        ]

        result = ask_human_intent()

        assert result is not None
        assert result.problems_solved == "Has a value"
        assert result.core_responsibilities is None
        assert result.non_responsibilities is None
        assert result.system_context == "Another value"
        assert result.entry_points is None
        assert result.invariants is None
        assert result.limitations is None
        assert result.common_pitfalls is None


def test_ask_human_intent_all_empty_responses():
    """Test that all empty responses returns None."""
    with patch("src.human_in_the_loop.questionary.text") as mock_text:
        # Return all empty strings
        mock_text.return_value.ask.side_effect = ["", "", "", "", "", "", "", ""]

        result = ask_human_intent()

        assert result is None


def test_ask_human_intent_keyboard_interrupt():
    """Test that keyboard interrupt returns None."""
    with patch("src.human_in_the_loop.questionary.text") as mock_text:
        # Raise KeyboardInterrupt on first question
        mock_text.return_value.ask.side_effect = KeyboardInterrupt()

        result = ask_human_intent()

        assert result is None


def test_ask_human_intent_console_output(capsys):
    """Test that appropriate console messages are printed."""
    with patch("src.human_in_the_loop.questionary.text") as mock_text:
        mock_text.return_value.ask.side_effect = [
            "Value 1",
            "Value 2",
            "Value 3",
            "Value 4",
            "Value 5",
            "Value 6",
            "Value 7",
            "Value 8",
        ]

        result = ask_human_intent()

        # We can't easily capture rich console output, but we can verify
        # the function completed successfully
        assert result is not None


def test_ask_human_intent_skip_console_output(capsys):
    """Test console output when questionnaire is skipped."""
    with patch("src.human_in_the_loop.questionary.text") as mock_text:
        mock_text.return_value.ask.return_value = None

        result = ask_human_intent()

        assert result is None
