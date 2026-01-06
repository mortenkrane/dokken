"""Input validation for prompt injection detection."""

import re
from dataclasses import dataclass
from typing import Literal


@dataclass
class ValidationResult:
    """Result of input validation."""

    is_suspicious: bool
    warnings: list[str]
    severity: Literal["low", "medium", "high"]


# Patterns that suggest prompt injection attempts
SUSPICIOUS_PATTERNS = [
    # Direct instruction attempts
    (
        r"\b(ignore|disregard|forget)\s+((all\s+)?(previous|prior)\s+|(all\s+))(instructions?|tasks?|prompts?)",
        "Contains instruction to ignore previous directives",
        "high",
    ),
    # System message impersonation
    (
        r"\b(system|important|critical)\s*(override|instruction|message|directive)",
        "Attempts to impersonate system instructions",
        "high",
    ),
    # Task redefinition
    (
        r"\b(new|real|actual)\s+(task|instruction|goal|objective)",
        "Attempts to redefine the task",
        "high",
    ),
    # Priority manipulation
    (r"\bhighest\s+priority\b", "Attempts to manipulate priority", "medium"),
    # Response format manipulation
    (
        r"\brespond\s+with\b.*\b(json|markdown|code)\b",
        "Attempts to control response format",
        "medium",
    ),
    # Common jailbreak markers
    (
        r"\[/?(system|assistant|user|end|start)\]",
        "Contains markup that could confuse LLM context",
        "medium",
    ),
    # Role manipulation
    (r"\byou\s+are\s+(now|actually|really)\b", "Attempts to redefine LLM role", "high"),
]


def validate_custom_prompt(prompt: str) -> ValidationResult:
    """
    Validate a custom prompt for suspicious patterns.

    Args:
        prompt: The custom prompt text to validate.

    Returns:
        ValidationResult with detected issues.
    """
    if not prompt:
        return ValidationResult(is_suspicious=False, warnings=[], severity="low")

    warnings = []
    max_severity = "low"

    for pattern, warning, severity in SUSPICIOUS_PATTERNS:
        if re.search(pattern, prompt, re.IGNORECASE):
            warnings.append(f"{warning} (pattern: {pattern})")
            if severity == "high":
                max_severity = "high"
            elif severity == "medium" and max_severity == "low":
                max_severity = "medium"

    return ValidationResult(
        is_suspicious=len(warnings) > 0,
        warnings=warnings,
        severity=max_severity,
    )


def validate_code_context(
    context: str, max_sample_size: int = 10000
) -> ValidationResult:
    """
    Validate code context for suspicious comment patterns.

    Note: This checks a sample of the context to avoid performance issues
    on large codebases.

    Args:
        context: Code context string to validate.
        max_sample_size: Maximum characters to sample for validation.

    Returns:
        ValidationResult with detected issues (lower severity than prompts).
    """
    # Sample first and last portions of context
    sample = context[: max_sample_size // 2] + context[-max_sample_size // 2 :]

    warnings = []

    # Look for comment blocks that look like instructions
    instruction_pattern = r"#.*\b(important|critical|system).*instruction"
    if re.search(instruction_pattern, sample, re.IGNORECASE):
        warnings.append(
            "Code comments contain instruction-like language. "
            "Review for potential prompt injection in docstrings."
        )

    # Check for suspicious "IMPORTANT:" patterns in comments
    important_override = r"#.*IMPORTANT:.*\b(ignore|override|instead)\b"
    if re.search(important_override, sample, re.IGNORECASE):
        warnings.append("Code comments contain suspicious override patterns.")

    return ValidationResult(
        is_suspicious=len(warnings) > 0,
        warnings=warnings,
        severity="low",  # Code comments are always lower risk than custom prompts
    )
