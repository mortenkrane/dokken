"""Tests for src/git.py"""

from pytest_mock import MockerFixture

from src.git import setup_git


def test_setup_git_smoke(mocker: MockerFixture, mock_console) -> None:
    """Smoke test that setup_git executes all git commands."""
    # Mock subprocess.run to avoid actual git commands
    mock_subprocess = mocker.patch("src.git.subprocess.run")

    # Mock datetime to make branch name deterministic
    mock_datetime = mocker.patch("src.git.datetime")
    mock_datetime.now.return_value.strftime.return_value = "2024-01-15"

    # Execute
    setup_git()

    # Verify all three git commands were called
    assert mock_subprocess.call_count == 3

    # Verify git checkout main
    mock_subprocess.assert_any_call(
        ["git", "checkout", "main"],
        check=True,
        capture_output=True,
    )

    # Verify git pull
    mock_subprocess.assert_any_call(
        ["git", "pull"],
        check=True,
        capture_output=True,
    )

    # Verify git checkout -b with dated branch name
    mock_subprocess.assert_any_call(
        ["git", "checkout", "-b", "dokken/docs-2024-01-15"],
        check=True,
        capture_output=True,
    )
