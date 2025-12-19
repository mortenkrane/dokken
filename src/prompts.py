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


DOCUMENTATION_GENERATION_PROMPT = """You are an expert technical writer creating
developer-focused documentation. Your goal is to help developers quickly understand and
work with this codebase.

Analyze the code context and generate comprehensive documentation that covers:

1. **Purpose & Scope**: What this component does and its boundaries (2-3 paragraphs)

2. **Architecture Overview**: How the component is structured - key modules, their
   interactions, data flow patterns, and overall design

3. **Main Entry Points**: The primary functions, classes, or CLI commands developers
   use to interact with this component. For each entry point, explain what it does and
   when to use it

4. **Control Flow**: How requests or operations flow through the system from start to
   finish. Trace the key execution paths, decision points, and data transformations

5. **Key Design Decisions**: The most important architectural choices and WHY they were
   made. Write this as flowing prose, not bullet points. Explain patterns, technologies,
   and approaches in a cohesive narrative that helps developers understand the rationale

6. **External Dependencies**: Third-party libraries, APIs, or systems used and what
   role they play

Focus on information that helps developers:
- Understand the system's architecture quickly
- Know where to start when making changes
- Trace how data and control flow through the code
- Understand why certain design choices were made

Do NOT include:
- Function signature details (those belong in docstrings)
- Line-by-line code explanations
- Installation or setup instructions

--- CODE CONTEXT ---
{context}

Respond ONLY with the JSON object schema provided."""
