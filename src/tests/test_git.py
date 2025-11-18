"""Tests for src/git.py"""

from datetime import datetime
from unittest.mock import call

import pytest

from src.git import GIT_BASE_BRANCH, setup_git


def test_git_base_branch_constant():
    """Test that GIT_BASE_BRANCH is set to 'main'."""
    assert GIT_BASE_BRANCH == "main"


def test_setup_git_checks_out_main(mocker):
    """Test that setup_git checks out the main branch."""
    mock_subprocess = mocker.patch("src.git.subprocess.run")
    mocker.patch("src.git.console")

    setup_git()

    # Check that checkout main was called
    checkout_call = call(
        ["git", "checkout", GIT_BASE_BRANCH],
        check=True,
        capture_output=True,
    )
    assert checkout_call in mock_subprocess.call_args_list


def test_setup_git_pulls_latest(mocker):
    """Test that setup_git pulls the latest changes."""
    mock_subprocess = mocker.patch("src.git.subprocess.run")
    mocker.patch("src.git.console")

    setup_git()

    # Check that git pull was called
    pull_call = call(["git", "pull"], check=True, capture_output=True)
    assert pull_call in mock_subprocess.call_args_list


def test_setup_git_creates_branch_with_date(mocker):
    """Test that setup_git creates a new branch with current date."""
    mock_subprocess = mocker.patch("src.git.subprocess.run")
    mocker.patch("src.git.console")
    mock_datetime = mocker.patch("src.git.datetime")
    mock_datetime.now.return_value = datetime(2025, 11, 18)

    setup_git()

    # Check that branch creation was called with correct format
    expected_branch = "dokken/docs-2025-11-18"
    branch_call = call(
        ["git", "checkout", "-b", expected_branch],
        check=True,
        capture_output=True,
    )
    assert branch_call in mock_subprocess.call_args_list


def test_setup_git_operations_order(mocker):
    """Test that setup_git executes git operations in the correct order."""
    mock_subprocess = mocker.patch("src.git.subprocess.run")
    mocker.patch("src.git.console")
    mock_datetime = mocker.patch("src.git.datetime")
    mock_datetime.now.return_value = datetime(2025, 11, 18)

    setup_git()

    # Get the order of calls
    calls = mock_subprocess.call_args_list

    # Should be: 1. checkout main, 2. pull, 3. create new branch
    assert len(calls) == 3
    assert calls[0][0][0] == ["git", "checkout", GIT_BASE_BRANCH]
    assert calls[1][0][0] == ["git", "pull"]
    assert calls[2][0][0] == ["git", "checkout", "-b", "dokken/docs-2025-11-18"]


@pytest.mark.parametrize(
    "date,expected_branch",
    [
        (datetime(2025, 1, 1), "dokken/docs-2025-01-01"),
        (datetime(2025, 12, 31), "dokken/docs-2025-12-31"),
        (datetime(2024, 6, 15), "dokken/docs-2024-06-15"),
    ],
)
def test_setup_git_branch_name_format(mocker, date, expected_branch):
    """Test that setup_git creates correctly formatted branch names for various dates."""
    mock_subprocess = mocker.patch("src.git.subprocess.run")
    mocker.patch("src.git.console")
    mock_datetime = mocker.patch("src.git.datetime")
    mock_datetime.now.return_value = date

    setup_git()

    # Check the last call (branch creation)
    last_call = mock_subprocess.call_args_list[-1]
    assert expected_branch in last_call[0][0]


def test_setup_git_prints_status_messages(mocker):
    """Test that setup_git prints status messages to console."""
    mocker.patch("src.git.subprocess.run")
    mock_console = mocker.patch("src.git.console")

    setup_git()

    # Verify console.print was called multiple times
    assert mock_console.print.call_count >= 3
    assert mock_console.status.call_count >= 3


def test_setup_git_handles_subprocess_check(mocker):
    """Test that setup_git passes check=True to all subprocess calls."""
    mock_subprocess = mocker.patch("src.git.subprocess.run")
    mocker.patch("src.git.console")

    setup_git()

    # All subprocess calls should have check=True
    for call_args in mock_subprocess.call_args_list:
        assert call_args[1]["check"] is True


def test_setup_git_captures_output(mocker):
    """Test that setup_git captures subprocess output."""
    mock_subprocess = mocker.patch("src.git.subprocess.run")
    mocker.patch("src.git.console")

    setup_git()

    # All subprocess calls should have capture_output=True
    for call_args in mock_subprocess.call_args_list:
        assert call_args[1]["capture_output"] is True
