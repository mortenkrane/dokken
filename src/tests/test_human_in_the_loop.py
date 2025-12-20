"""Tests for the human-in-the-loop questionnaire functionality."""

from unittest.mock import patch

from src.human_in_the_loop import ask_human_intent
from src.records import ModuleIntent


def test_ask_human_intent_full_responses():
    """Test questionnaire with full responses for all questions."""
    # Mock questionary to return specific answers
    with patch("src.human_in_the_loop.questionary.text") as mock_text:
        mock_text.return_value.ask.side_effect = [
            "Handles payment processing",
            "Payment gateway integration",
            "Tax calculation",
            "Part of e-commerce system",
        ]

        result = ask_human_intent()

        assert result is not None
        assert isinstance(result, ModuleIntent)
        assert result.problems_solved == "Handles payment processing"
        assert result.core_responsibilities == "Payment gateway integration"
        assert result.non_responsibilities == "Tax calculation"
        assert result.system_context == "Part of e-commerce system"


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
        # Answer first two, skip last two
        mock_text.return_value.ask.side_effect = [
            "Handles authentication",  # Question 1
            "User login and registration",  # Question 2
            None,  # Question 3 - skipped
            None,  # Question 4 - skipped
        ]

        result = ask_human_intent()

        assert result is not None
        assert isinstance(result, ModuleIntent)
        assert result.problems_solved == "Handles authentication"
        assert result.core_responsibilities == "User login and registration"
        assert result.non_responsibilities is None
        assert result.system_context is None


def test_ask_human_intent_empty_responses():
    """Test that empty string responses are converted to None."""
    with patch("src.human_in_the_loop.questionary.text") as mock_text:
        # Return empty strings
        mock_text.return_value.ask.side_effect = [
            "Has a value",
            "",  # Empty string
            "   ",  # Whitespace only
            "Another value",
        ]

        result = ask_human_intent()

        assert result is not None
        assert isinstance(result, ModuleIntent)
        assert result.problems_solved == "Has a value"
        assert result.core_responsibilities is None
        assert result.non_responsibilities is None
        assert result.system_context == "Another value"


def test_ask_human_intent_all_empty_responses():
    """Test that all empty responses returns None."""
    with patch("src.human_in_the_loop.questionary.text") as mock_text:
        # Return all empty strings
        mock_text.return_value.ask.side_effect = ["", "", "", ""]

        result = ask_human_intent()

        assert result is None


def test_ask_human_intent_keyboard_interrupt():
    """Test that keyboard interrupt returns None."""
    with patch("src.human_in_the_loop.questionary.text") as mock_text:
        # Raise KeyboardInterrupt on first question
        mock_text.return_value.ask.side_effect = KeyboardInterrupt()

        result = ask_human_intent()

        assert result is None
