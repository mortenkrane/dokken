"""LLM prompt templates for documentation generation and drift detection.

These prompts can be easily modified and A/B tested without changing the core logic.
"""

DRIFT_CHECK_PROMPT = """You are a Documentation Drift Detector. Your task is to
analyze if the current documentation accurately reflects the code context.

Use this checklist to determine drift. Drift is detected if ANY of these are true:

1. **Structural Changes**: The code shows major architectural changes (new modules,
   removed components, restructured packages) not reflected in documentation.
2. **Purpose Mismatch**: The documentation's stated purpose contradicts what the
   code actually does.
3. **Missing Key Features**: The code implements significant features/functionality
   that are not mentioned in the documentation.
4. **Outdated Design Decisions**: The documentation explains design decisions that
   are no longer present in the code.
5. **Incorrect Dependencies**: The documentation lists external dependencies that
   don't match what's in the code.

IMPORTANT: Do NOT flag drift for:
- Minor code changes (refactoring, variable renames, formatting)
- Code comments or docstring updates
- Implementation details not typically in high-level docs
- Additions that don't change the core purpose/architecture

--- CODE CONTEXT ---
{context}

--- CURRENT DOCUMENTATION ---
{current_doc}

Analyze methodically:
1. Read the documentation's claims about purpose and architecture
2. Check if the code context contradicts or significantly extends those claims
3. Apply the checklist above
4. Set drift_detected=true ONLY if at least one checklist item applies

Respond ONLY with the JSON object schema provided."""


DOCUMENTATION_GENERATION_PROMPT = """You are an expert technical writer. Based on the
provided code context, generate a complete, structured documentation overview.
Focus on the component's main purpose, scope, and the 'why' behind its design.
Do not include simple function signature details (assume those are in docstrings).
--- CODE CONTEXT ---
{context}
Respond ONLY with the JSON object schema provided."""
