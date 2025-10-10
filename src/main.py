import os
import subprocess
import sys
import glob
from typing import List

from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.program import LLMTextCompletionProgram

from src.records import DocumentationDriftCheck, ComponentDocumentation

GIT_BASE_BRANCH = "main"


def setup_git() -> None:
    """
    Sets up git for documentation generation:
    1. Checks out main branch
    2. Pulls latest changes
    3. Creates a new branch with format dokken/docs-<ISO date>
    """
    from datetime import datetime

    print("--- GIT SETUP ---")

    # 1. Checkout main
    subprocess.run(["git", "checkout", GIT_BASE_BRANCH], check=True)
    print("✅ Checked out main branch")

    # 2. Pull latest changes
    subprocess.run(["git", "pull"], check=True)
    print("✅ Pulled latest changes")

    # 3. Create new branch with ISO date format
    iso_date = datetime.now().strftime("%Y-%m-%d")
    branch_name = f"dokken/docs-{iso_date}"
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)
    print(f"✅ Created and checked out branch: {branch_name}")


def initialize_llm() -> GoogleGenAI:
    """Initializes the GoogleGenAI LLM client."""
    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY environment variable not set.")

    # Using Gemini-2.5-Flash as it has a good balance of speed, cost, and context window
    # Low temp for stability
    return GoogleGenAI(model="gemini-2.5-flash", temperature=0.0)


def get_module_context(*, module_path: str, base_branch: str = "main") -> str:
    """
    Fetches the full code content and the diff for all Python files in a module directory.

    Args:
        module_path: The path to the module directory to analyze.
        base_branch: The branch to diff against (e.g., 'main' or 'HEAD~1').

    Returns:
        A formatted string containing all Python files' content and diffs.
    """
    try:
        # Find all Python files in the module directory
        python_files = glob.glob(os.path.join(module_path, "*.py"))

        if not python_files:
            print(f"No Python files found in {module_path}")
            return ""

        context = f"--- MODULE PATH: {module_path} ---\n\n"

        for file_path in sorted(python_files):
            # 1. Get the current file content
            with open(file_path, "r") as f:
                code_content = f.read()

            # 2. Get the diff relative to the base branch
            result = subprocess.run(
                ["git", "diff", f"{base_branch}", "--", file_path],
                capture_output=True,
                text=True,
                check=True,
            )
            diff_content = result.stdout

            # Add file context
            context += (
                f"--- FILE: {file_path} ---\n"
                f"--- CURRENT CODE CONTENT ---\n{code_content}\n"
                f"--- CODE CHANGES (GIT DIFF vs. {base_branch}) ---\n{diff_content}\n\n"
            )

        return context
    except Exception as e:
        print(f"Error getting module context for {module_path}: {e}")
        return ""


def step_1_check_drift(
    *, llm: GoogleGenAI, context: str, current_doc: str
) -> DocumentationDriftCheck:
    """
    STEP 1: Ask the LLM to validate the current documentation against the code changes.
    """
    # Use LLMTextCompletionProgram for structured Pydantic output
    check_program = LLMTextCompletionProgram.from_defaults(
        output_cls=DocumentationDriftCheck,
        llm=llm,
        prompt_template_str=(
            "You are a Documentation Drift Detector. Your task is to analyze the "
            "provided code context and the current documentation to determine if the "
            "documentation is now obsolete, inaccurate, or missing crucial information "
            "due to the code changes. Focus specifically on high-level structure, "
            "purpose, and design decisions. "
            "--- CODE CONTEXT & DIFF ---\n{context}\n"
            "--- CURRENT DOCUMENTATION ---\n{current_doc}\n"
            "Respond ONLY with the JSON object schema provided."
        ),
    )

    # Run the check
    check_result = check_program(context=context, current_doc=current_doc)
    return check_result


def step_2_generate_doc(*, llm: GoogleGenAI, context: str) -> ComponentDocumentation:
    """
    STEP 2: Generate the complete, new structured documentation for the component.
    """
    # Use LLMTextCompletionProgram for structured Pydantic output
    generate_program = LLMTextCompletionProgram.from_defaults(
        output_cls=ComponentDocumentation,
        llm=llm,
        prompt_template_str=(
            "You are an expert technical writer. Based on the provided code context, "
            "generate a complete, structured documentation overview. "
            "Focus on the component's main purpose, scope, and the 'why' behind its design. "
            "Do not include simple function signature details (assume those are in docstrings). "
            "--- CODE CONTEXT ---\n{context}\n"
            "Respond ONLY with the JSON object schema provided."
        ),
    )

    # Run the generation
    doc_result = generate_program(context=context)
    return doc_result


def generate_markdown(*, doc_data: ComponentDocumentation) -> str:
    """
    Converts the structured Pydantic data into a human-readable Markdown string.

    NOTE: This templating step is CRITICAL for output stability!
    """
    md = f"# {doc_data.component_name} Overview\n\n"
    md += f"## Purpose & Scope\n\n{doc_data.purpose_and_scope}\n\n"

    if doc_data.external_dependencies:
        md += f"## External Dependencies\n\n{doc_data.external_dependencies}\n\n"

    md += "## Key Design Decisions (The 'Why')\n\n"

    # Sort keys for deterministic output to prevent diff noise
    sorted_decisions = sorted(doc_data.design_decisions.items())

    for key, decision_text in sorted_decisions:
        md += f"### Decision: {key}\n\n"
        md += f"{decision_text}\n\n"

    return md


def generate_documentation(*, target_module_path: str) -> None:
    if not os.path.isdir(target_module_path):
        print(f"Error: {target_module_path} is not a valid directory")
        sys.exit(1)

    # Documentation will be written to README.md in the target module
    readme_path = os.path.join(target_module_path, "README.md")

    print(f"Target module: {target_module_path}")
    print(f"Documentation output: {readme_path}")

    # 0. Git setup
    setup_git()

    # 1. Setup
    llm_client = initialize_llm()
    code_context = get_module_context(
        module_path=target_module_path, base_branch=GIT_BASE_BRANCH
    )

    if not code_context:
        print("No code context found. Exiting.")
        return

    # Check for existing README.md
    if os.path.exists(readme_path):
        with open(readme_path, "r") as f:
            current_doc_content = f.read()
        print(f"Found existing README.md at {readme_path}")
    else:
        current_doc_content = "No existing documentation provided."
        print(f"No existing README.md found at {readme_path}")

    # 2. Step 1: Check for Documentation Drift
    print("--- STEP 1: Checking for documentation drift... ---")
    drift_check = step_1_check_drift(
        llm=llm_client, context=code_context, current_doc=current_doc_content
    )

    print(f"Drift Detected: {drift_check.drift_detected}")
    print(f"Rationale: {drift_check.rationale}")

    if (
        not drift_check.drift_detected
        and "No existing documentation provided." not in current_doc_content
    ):
        print("✅ Documentation is considered up-to-date. No new file generated.")
        return

    # 3. Step 2: Generate New Structured Documentation
    print("--- STEP 2: Generating new structured documentation... ---")
    new_doc_data = step_2_generate_doc(llm=llm_client, context=code_context)

    # 4. Generate Final Markdown (Stabilization)
    final_markdown = generate_markdown(doc_data=new_doc_data)

    # 5. Overwrite README.md with the new documentation
    with open(readme_path, "w") as f:
        f.write(final_markdown)

    print(f"📝 New documentation generated and saved to: {readme_path}")
    print("\n--- GENERATED DOCUMENTATION ---")
    print(final_markdown)


# --- Manual Execution ---

if __name__ == "__main__":
    # Get target module path from command line arguments
    if len(sys.argv) < 2:
        print("Usage: python main.py <module_path>")
        print("Example: python main.py src/payment_service")
        sys.exit(1)

    target_module_path = sys.argv[1]

    try:
        generate_documentation(target_module_path=target_module_path)
    except ValueError as e:
        print(f"Configuration Error: {e}")
