"""LLM prompt templates for documentation generation and drift detection.

These prompts can be easily modified and A/B tested without changing the core logic.
"""

DRIFT_CHECK_PROMPT = """You are a Documentation Drift Detector. Your task is to analyze the \
provided code context and the current documentation to determine if the \
documentation is now obsolete, inaccurate, or missing crucial information \
due to the code changes. Focus specifically on high-level structure, \
purpose, and design decisions. \
--- CODE CONTEXT & DIFF ---
{context}
--- CURRENT DOCUMENTATION ---
{current_doc}
Respond ONLY with the JSON object schema provided."""


DOCUMENTATION_GENERATION_PROMPT = """You are an expert technical writer. Based on the provided code context, \
generate a complete, structured documentation overview. \
Focus on the component's main purpose, scope, and the 'why' behind its design. \
Do not include simple function signature details (assume those are in docstrings). \
--- CODE CONTEXT ---
{context}
Respond ONLY with the JSON object schema provided."""
