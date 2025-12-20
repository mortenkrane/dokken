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


MODULE_GENERATION_PROMPT = """You are an expert technical writer creating
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
{human_intent_section}
Respond ONLY with the JSON object schema provided."""


PROJECT_README_GENERATION_PROMPT = """You are an expert technical writer creating a
top-level README for a software project. Your goal is to introduce the project to new
users and contributors clearly and concisely.

Analyze the code context and generate comprehensive project documentation that covers:

1. **Project Purpose**: What problem does this project solve? Why does it exist? Write
   2-3 paragraphs introducing the project to new users.

2. **Key Features**: Main capabilities of the project. Provide a bulleted list of 3-7
   features that users should know about.

3. **Installation**: How users install and set up the project for usage. Include
   prerequisites, installation steps, and basic configuration.

4. **Development Setup**: How contributors set up the project for development. Include
   installing dependencies, running tests, and any dev tools.

5. **Usage Examples**: Basic usage patterns and commands. Show the most common use cases
   with concrete examples that users can copy and run.

6. **Project Structure**: High-level overview of directory organization. Help users
   understand where to find different components without overwhelming detail.

7. **Contributing** (optional): How to contribute to the project. Include PR process,
   coding standards, or note if there's a separate CONTRIBUTING.md.

Focus on:
- Clear, welcoming introduction for new users
- Practical setup instructions for both usage and development
- Concrete examples users can actually run
- High-level understanding of project layout

Do NOT include:
- Deep architectural details (those go in module READMEs)
- API reference documentation (use dedicated API docs)
- Marketing language or excessive hype
- Implementation details

--- CODE CONTEXT ---
{context}
{human_intent_section}
Respond ONLY with the JSON object schema provided."""


STYLE_GUIDE_GENERATION_PROMPT = """You are an expert technical writer analyzing code
patterns to extract coding conventions. Your goal is to document the *actual* patterns
used in this codebase, not generic best practices.

Analyze the code context and extract the following:

1. **Languages**: Programming languages used in this project. Provide a list.

2. **Code Style Patterns**: Formatting, naming conventions, and code structure
   patterns consistently used across the codebase. Include specific examples from
   the code.

3. **Architectural Patterns**: Design patterns, abstractions, and architectural
   approaches used in the codebase. Explain dependency injection, data flow,
   separation of concerns, and other patterns. Reference specific modules or
   functions.

4. **Testing Conventions**: Test structure, mocking patterns, fixtures, and testing
   practices. Explain how tests are organized, what patterns to follow, and provide
   examples.

5. **Git Workflow**: Branching strategy, commit message format, PR process, and version
   control practices. Look for commit conventions (Conventional Commits, etc.).

6. **Module Organization**: How code is organized into modules, packages, and files.
   Explain the directory structure and module responsibilities.

7. **Dependencies Management**: How dependencies are declared, managed, and
   versioned. Include package management tools and practices (requirements.txt,
   pyproject.toml, etc.).

Focus on:
- Patterns that appear consistently across multiple files
- Specific examples from the codebase (file paths, function names)
- Conventions that new contributors should follow
- Differences from standard practices (if any)

Do NOT include:
- Generic best practices not evidenced in the code
- Prescriptive rules not currently followed
- Implementation details of specific features
- Every minor variation (focus on common patterns)

--- CODE CONTEXT ---
{context}
{human_intent_section}
Respond ONLY with the JSON object schema provided."""


# Backward compatibility alias
DOCUMENTATION_GENERATION_PROMPT = MODULE_GENERATION_PROMPT
