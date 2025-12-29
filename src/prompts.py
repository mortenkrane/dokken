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

FORMATTING GUIDELINES:
- Use scannable bullet lists instead of dense paragraphs where appropriate
- Front-load keywords in each section (put important terms first)
- Include file references, but without specific line numbers (e.g., "see
`module_name.py`", not "see `module_name.py:45`"))
- Make content easy to grep/search (use consistent terminology)
- Use **bold** for key terms and concepts

Analyze the code context and generate comprehensive documentation that covers:

1. **Main Entry Points**: The primary functions, classes, or CLI commands developers
   use to interact with this component. Format as a bulleted or structured list.
   For each entry point:
   - Function/class name
   - What it does (one line)
   - When to use it
   - Key parameters or usage notes

2. **Purpose & Scope**: What this component does and its boundaries (2-3 paragraphs).
   Start with a keyword-rich first sentence that defines the module's role.

3. **Architecture Overview**: How the component is structured. Use lists or subsections:
   - Key modules/files and their responsibilities
   - How components interact
   - Data flow patterns
   - Overall structure

4. **Control Flow**: How requests or operations flow through the system. Use numbered
   steps or bullet points to trace execution paths. Include:
   - Entry points and triggers
   - Key decision points
   - Data transformations
   - Exit conditions

5. **Control Flow Diagram** (optional): If the control flow has meaningful decision
   points or branching logic, create a Mermaid flowchart diagram to visualize it. Use
   Mermaid flowchart syntax (```mermaid flowchart TD```). Create butterfly-style
   diagrams where appropriate, showing how execution branches and reconverges. Include:
   - Entry points (use rounded rectangles)
   - Decision points (use diamonds for conditionals)
   - Process steps (use rectangles)
   - Data flow arrows with labels
   - Exit points or return paths
   Example structure: Entry → Decision → Branch A/B → Processing → Converge → Exit
   Skip this if the flow is purely linear with no meaningful branches

6. **Key External Dependencies**: Core third-party libraries that are essential to this
   module's functionality. Focus ONLY on dependencies that:
   - Define what the module does (e.g., LLM SDKs for AI features, web frameworks for
   APIs)
   - Are central to the module's core purpose
   - Would require significant refactoring to replace

   EXCLUDE:
   - Standard library imports (os, sys, pathlib, etc.)
   - Internal imports from the same project
   - Generic utility libraries (typing, dataclasses, etc.)
   - Common infrastructure (logging, testing frameworks)

   Format as:
   - **Dependency name**: What it's used for and why it's key

   If there are no key external dependencies, omit this section entirely

7. **Key Design Decisions**: The most important architectural choices and WHY they were
   made. Write this as flowing prose, not bullet points. Explain patterns, technologies,
   and approaches in a cohesive narrative that helps developers understand the rationale

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

FORMATTING GUIDELINES FOR SEARCH/REFERENCE OPTIMIZATION:
- Use scannable bullet lists and code blocks (not dense paragraphs)
- Front-load keywords in sections (important terms first)
- Create clear hierarchies with headers and subheaders
- Include concrete commands users can copy-paste
- Use **bold** for key terms, `code formatting` for commands/files
- Make content grep-friendly (use consistent, searchable terms)

Analyze the code context and generate comprehensive project documentation that covers:

1. **Usage Examples**: Basic usage patterns and commands. Start with the most common
   use cases. Format as:
   - Clear command examples with descriptions
   - Copy-pastable code blocks
   - Multiple use cases if relevant
   Show users how to actually use the project before explaining installation.

2. **Installation**: How users install and set up the project. Structure clearly:
   - Prerequisites (with version numbers if applicable)
   - Installation steps (numbered, with actual commands)
   - Configuration (environment variables, config files)
   Use code blocks for commands users can copy directly.

3. **Key Features**: Main capabilities. Provide a bulleted list of 3-7 features.
   Each bullet should:
   - Start with the feature name in bold
   - Describe what it does (one line)

4. **Project Purpose**: What problem does this project solve? Write 2-3 paragraphs
   with a keyword-rich first sentence that immediately identifies what this is.

5. **Project Structure**: High-level directory organization. Format as a tree or
   structured list:
   ```
   src/
     module_name/ - What this module does
     other_module/ - What this does
   ```
   Include one-line descriptions for each major directory.

6. **Development**: How contributors set up for development. Structure with subheaders:
   - **Dev Setup**: Installation commands
   - **Running Tests**: Test commands with examples
   - **Code Quality**: Linting, formatting commands
   - **Documentation**: Links to style guides or contributing docs

7. **Contributing** (optional): How to contribute. Keep brief or link to
   CONTRIBUTING.md.

Focus on:
- Commands and examples users can immediately run
- Clear, hierarchical structure for easy navigation
- Scannable format (both human and AI readers)
- Practical, actionable information

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

FORMATTING GUIDELINES:
- Use clear subsections with descriptive headers
- Provide concrete code examples (not just descriptions)
- Include file references for patterns (e.g., "see `module.py`"), but omit line numbers
- Use bullet lists for conventions and patterns
- Make content scannable and reference-friendly

Analyze the code context and extract the following:

1. **Languages & Tools**: Programming languages used in this project. List with
   versions if detectable.

2. **Code Style**: Formatting, naming conventions, and code structure patterns.
   Structure with subsections:
   - **Naming Conventions**: How variables, functions, classes are named (with examples)
   - **Formatting**: Indentation, line length, import ordering (reference actual code)
   - **Code Structure**: Common patterns for organizing functions and classes

3. **Testing Conventions**: Test structure and practices. Break down into:
   - **Test Organization**: Where tests live, file naming patterns
   - **Test Structure**: How tests are written (function-based vs class-based)
   - **Mocking & Fixtures**: Common patterns with examples
   - **Running Tests**: Commands to execute tests
   Include file references to example tests, without line numbers.

4. **Architecture & Patterns**: Design patterns and architectural approaches.
   Organize by pattern type:
   - **Dependency Injection**: How dependencies are passed
   - **Data Flow**: How data moves through the system
   - **Separation of Concerns**: Module responsibilities
   Reference specific modules that demonstrate each pattern.

5. **Module Organization**: How code is organized. Provide:
   - Directory structure (tree format if possible)
   - Module responsibilities (what each directory/file does)
   - File naming conventions

6. **Git Workflow**: Version control practices. Include:
   - **Commit Format**: Message conventions (e.g., Conventional Commits)
   - **Branching**: Strategy for branches
   - **PR Process**: How pull requests work
   Provide examples of good commit messages.

7. **Dependencies**: How dependencies are managed. Include:
   - **Tools**: Package managers used (pip, poetry, uv, etc.)
   - **Declaration**: Where dependencies are listed (file names)
   - **Versioning**: How versions are specified
   - **Update Process**: How dependencies are updated

Focus on:
- Patterns that appear consistently across multiple files
- Specific examples from the codebase (file paths, function names)
- Conventions that new contributors should follow
- Differences from standard practices (if any)
- Clear, actionable guidelines with references

Do NOT include:
- Generic best practices not evidenced in the code
- Prescriptive rules not currently followed
- Implementation details of specific features
- Every minor variation (focus on common patterns)

--- CODE CONTEXT ---
{context}
{human_intent_section}
Respond ONLY with the JSON object schema provided."""


INCREMENTAL_FIX_PROMPT = """You are a Documentation Maintenance Specialist.
Your task is to make MINIMAL, TARGETED changes to existing documentation to fix
specific drift issues.

CRITICAL CONSTRAINTS:
- Make ONLY the changes necessary to address the detected drift
- PRESERVE the existing structure, tone, and style
- DO NOT regenerate sections that are still accurate
- Keep changes surgical and focused
- Respect the original documentation's voice and formatting

Your goal is to fix what's wrong while keeping what's right.

APPROACH:
1. Read the existing documentation carefully
2. Identify which specific sections are affected by the drift issues
3. Determine the minimal change needed to fix each issue
4. Update ONLY those sections, preserving everything else
5. Maintain consistency with the original documentation's style

CHANGE TYPES:
- **update**: Modify existing section content (e.g., outdated function signature,
  incorrect description). IMPORTANT: Provide the COMPLETE section content with your
  changes integrated, preserving all parts that are still accurate.
- **add**: Add new section or content (e.g., document a new feature that was added)
- **remove**: Remove obsolete content (e.g., deleted functions, deprecated features)

SECTION TARGETING:
When identifying sections to change, use the exact section headers from the existing
documentation. Common sections include:
- Main Entry Points
- Purpose & Scope
- Architecture Overview
- Control Flow
- External Dependencies
- Key Design Decisions

For each change:
- Reference the specific drift issue you're addressing
- For **update** changes: Provide the COMPLETE section content with changes merged in,
  preserving all accurate existing content and integrating your updates
- For **add** changes: Provide the complete content for the new section
- Keep the section's original structure and formatting style
- Maintain consistency with adjacent sections

--- EXISTING DOCUMENTATION ---
{current_doc}

--- CODE CONTEXT ---
{context}

--- DETECTED DRIFT ISSUES ---
{drift_rationale}

{custom_prompts_section}

IMPORTANT INSTRUCTIONS:
1. Analyze the drift issues and determine which sections need updates
2. For each affected section with change_type="update":
   - CRITICAL: You MUST include ALL existing content from that section
   - Merge your changes INTO the existing content, don't replace it
   - Think of it as editing the section, not rewriting it
   - Only the specific outdated/incorrect parts should change
3. For sections marked as preserved_sections: Do NOT include them in changes list
4. Maintain the original documentation's style and tone
5. If custom prompts are provided above, apply them to your changes

COMMON MISTAKE TO AVOID:
❌ WRONG: Returning only the new/changed bullet points for an "update"
✓ CORRECT: Returning the FULL section with new bullet points added and old ones preserved

Respond with the structured JSON output schema provided."""
