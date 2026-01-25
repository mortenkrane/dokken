# Architectural Documentation Implementation Plan

## Executive Summary

This document outlines the design and implementation plan for adding **architectural documentation** to dokken. This feature introduces a complementary documentation mode where architecture is documented first as "what is" (LLM extracts essence from code), then refined by users to "what should be" (prescriptive constraints), and finally enforced against the codebase.

**Core Distinction:**

- **Technical Documentation** (current): Code is truth, docs describe implementation details
- **Architectural Documentation** (new): User-refined architecture is truth, code must comply

**Key Insight:** We don't prescribe which architectural rules to support. Users define their own architecture in free-form markdown sections, and the LLM interprets those sections to check compliance.

______________________________________________________________________

## Motivation

### Problem Statement

Dokken currently excels at keeping documentation synchronized with code changes. However, it lacks a mechanism to:

1. **Capture architectural intent** that isn't obvious from reading code
1. **Enforce architectural constraints** before they are violated
1. **Prevent regression** of intentional design decisions
1. **Document high-level architecture** separately from implementation details

### Use Cases

**Use Case 1: Layered Architecture**

```
ARCHITECTURE.md:
"The system MUST maintain three distinct layers:
API layer (api/) handles HTTP only, Domain layer (domain/)
contains business logic, Data layer (data/) handles persistence.
Domain MUST NOT import from API or Data layers."

Violation: domain/payment.py imports from data/repository.py
Result: CI fails - layer boundary violated
```

**Use Case 2: Transaction Boundaries**

```
ARCHITECTURE.md:
"All payment operations MUST be atomic. Any operation touching
both Payment and Ledger tables MUST run in a single transaction."

Violation: New payment flow commits Payment before updating Ledger
Result: CI fails - transaction boundary violated
```

**Use Case 3: Abstraction Enforcement**

```
ARCHITECTURE.md:
"External service communication MUST go through the PaymentGateway
abstraction. Direct HTTP calls to the processor are forbidden."

Violation: New feature makes direct requests.post() to processor
Result: CI fails - abstraction bypassed
```

**Note:** These are architectural concepts that AST-based linters can't check. We focus on high-level patterns, not syntax.

______________________________________________________________________

## Conceptual Model

### Two Documentation Types

| Aspect                   | Technical Docs                     | Architectural Docs                       |
| ------------------------ | ---------------------------------- | ---------------------------------------- |
| **Truth Source**         | Code                               | User-refined ARCHITECTURE.md             |
| **Purpose**              | Describe implementation            | Define architectural constraints         |
| **Content**              | Entry points, APIs, dependencies   | Layers, boundaries, patterns, invariants |
| **Drift Direction**      | Code changes → Docs update         | Code must comply → Docs rarely change    |
| **Location**             | `README.md`                        | `ARCHITECTURE.md`                        |
| **Tone**                 | Descriptive ("The system uses...") | Prescriptive ("The system MUST...")      |
| **Update Frequency**     | Often (follows code)               | Rarely (deliberate decisions)            |
| **CI Behavior on Drift** | Optional (can defer fixes)         | Blocking (must fix to merge)             |
| **Structure**            | Predefined sections                | User-defined sections                    |

### Three-Phase Workflow

```
Phase 1: GENERATE (LLM extracts architecture)
├─ LLM analyzes code
├─ Identifies architectural patterns
└─ Generates ARCHITECTURE.md describing "what is"

Phase 2: REFINE (User makes prescriptive)
├─ User manually edits ARCHITECTURE.md
├─ Changes "uses" → "MUST use"
├─ Adds constraints not evident in code
├─ Organizes into sections that matter
└─ Removes implementation details

Phase 3: ENFORCE (LLM checks compliance)
├─ LLM reads user-refined ARCHITECTURE.md
├─ Checks if code violates any sections
└─ Reports violations (fails CI if found)
```

**Example Evolution:**

```markdown
# Generated (Phase 1 - Descriptive)
## Layering
The codebase uses a three-layer architecture with API,
domain, and data modules. The domain layer imports from
both API and data layers.

# Refined (Phase 2 - Prescriptive)
## Layering
The system MUST maintain three distinct layers:
- API layer (api/) - HTTP handling only
- Domain layer (domain/) - Business logic
- Data layer (data/) - Database access

The domain layer MUST NOT import from API or data layers.

# Enforced (Phase 3)
dokken check src --arch-docs
→ ❌ Violation: domain/service.py imports from data/repository.py
```

______________________________________________________________________

## Architecture Design

### Command Structure

#### New Commands

```bash
# Generate initial architectural documentation (descriptive)
dokken generate <module> --arch-docs

# Check code compliance with architectural documentation
dokken check <module> --arch-docs

# Check all modules (CI mode)
dokken check --all --arch-docs

# Show what would be checked without failing
dokken check <module> --arch-docs --dry-run
```

#### User Workflow

```bash
# 1. Generate initial ARCHITECTURE.md
dokken generate src --arch-docs

# 2. User manually refines ARCHITECTURE.md:
#    - Change descriptive → prescriptive
#    - Add constraints not in code
#    - Remove implementation details
#    - Organize into meaningful sections

# 3. Configure enforcement in .dokken.toml
cat >> .dokken.toml <<EOF
[architectural_docs]
enabled = true
sections = ["Layering", "Boundaries"]  # or ["*"] for all
severity = "blocking"
EOF

# 4. Check compliance (fails if violations found)
dokken check src --arch-docs

# 5. Add to CI
# .github/workflows/ci.yml
- run: dokken check --all --arch-docs
```

### Configuration (`.dokken.toml`)

```toml
# Existing configuration
modules = ["src/auth", "src/api", "src/data"]
file_types = [".py"]

# Architectural documentation configuration
[architectural_docs]
# Enable architectural documentation checking
enabled = true

# Output filename (default: ARCHITECTURE.md)
output_filename = "ARCHITECTURE.md"

# Sections to enforce (default: all sections)
# Use ["*"] for all, or list specific section names
sections = ["*"]  # or ["Layering", "Boundaries", "Patterns"]

# Severity: "blocking" (fail CI), "warning" (log only), "advisory" (info)
severity = "blocking"

# Skip sections matching these patterns
skip_sections = ["Future Plans", "Historical Context"]

# Module-specific overrides
[modules.src_auth.architectural_docs]
severity = "blocking"  # Auth must always pass

[modules.src_experimental.architectural_docs]
severity = "advisory"  # Experimental code gets warnings only

[modules.src_legacy.architectural_docs]
enabled = false  # Don't check legacy code
```

### Data Models

#### Simple Violation Report Model

```python
# src/records.py

from pydantic import BaseModel, Field


class ArchitecturalViolation(BaseModel):
    """A detected violation of architectural documentation."""

    section_name: str = Field(
        description="Name of the section violated (e.g., 'Layering')"
    )
    severity: str = Field(
        description="blocking, warning, advisory"
    )
    violation_description: str = Field(
        description="What constraint was violated"
    )
    affected_files: list[str] = Field(
        description="Files that violate the constraint"
    )
    suggested_fix: str = Field(
        description="How to fix the violation"
    )
    code_excerpts: list[str] = Field(
        default_factory=list,
        description="Relevant code snippets"
    )


class ArchitecturalComplianceCheck(BaseModel):
    """Result of checking code against architectural documentation."""

    compliant: bool
    violations: list[ArchitecturalViolation]
    summary: str
    sections_checked: list[str]
```

**Note:** No predefined rule structures. The LLM interprets free-form markdown sections.

______________________________________________________________________

## LLM Prompts

### Prompt 1: Extract Architectural Essence (Generation)

```python
# src/llm/prompts.py

ARCHITECTURAL_EXTRACTION_PROMPT = """
You are analyzing a codebase to extract its high-level architecture.

Your task is to identify and document ARCHITECTURAL PATTERNS, not implementation details.

Focus on:
- **Layering**: What layers/modules exist? How do they relate?
- **Boundaries**: What are the major component boundaries?
- **Patterns**: What architectural patterns are used? (Repository, Factory, Strategy, etc.)
- **Data Flow**: How does data flow through the system?
- **External Dependencies**: What external systems/services are used?
- **Invariants**: What architectural invariants exist? (e.g., "all DB access goes through repositories")

Do NOT document:
- Implementation details (specific functions, classes)
- Code style or naming conventions
- Low-level logic or algorithms
- Anything checkable by AST-based linters (imports, syntax)

Write in DESCRIPTIVE tone (not prescriptive yet - user will refine):
- "The system uses..." (not "The system MUST use...")
- "Components communicate via..." (not "Components MUST communicate via...")

Output Format:
- Free-form markdown with section headings
- Organize into logical sections (user will refine these)
- Include Mermaid diagrams where helpful
- Keep it concise - focus on essence, not details

<code_context>
{code_context}
</code_context>

<custom_prompts>
{custom_prompts}
</custom_prompts>

Generate architectural documentation as markdown text (not a structured schema).
"""
```

### Prompt 2: Check Architectural Compliance (Enforcement)

```python
ARCHITECTURAL_COMPLIANCE_CHECK_PROMPT = """
You are checking if code complies with documented architectural constraints.

CRITICAL: The architectural documentation is TRUTH. Code must comply with it.

You will receive:
1. Current codebase
2. User-refined ARCHITECTURE.md (contains prescriptive constraints)
3. Configuration specifying which sections to check

Your task:
1. Parse the architectural documentation sections
2. For each section configured for checking:
   - Understand the architectural constraint it describes
   - Check if current code violates that constraint
3. Report violations with specific details

Focus on HIGH-LEVEL ARCHITECTURAL violations:
✅ Check for:
- Layer boundary violations (e.g., domain importing from data)
- Pattern violations (e.g., DB access bypassing repository)
- Abstraction bypasses (e.g., direct external API calls)
- Transaction boundary violations
- Security boundary violations
- Architectural invariants broken

❌ Do NOT flag:
- Import statements of allowed dependencies (leave to AST linters)
- Code style, formatting, naming conventions
- Implementation details within allowed boundaries
- Refactoring that preserves architectural intent
- Minor changes that don't violate documented constraints

For each violation:
- Identify which section is violated
- Explain what constraint was violated
- List specific files/code that violate it
- Suggest how to fix it

<code_context>
{code_context}
</code_context>

<architectural_documentation>
{architectural_documentation}
</architectural_documentation>

<sections_to_check>
{sections_to_check}
</sections_to_check>

<custom_prompts>
{custom_prompts}
</custom_prompts>

Output violations using the ArchitecturalComplianceCheck schema.
If code is compliant, return compliant=true with empty violations list.
"""
```

______________________________________________________________________

## Workflow Implementation

### Generate Architectural Documentation Workflow

```python
# src/workflows.py

async def generate_architectural_docs(
    module_path: Path,
    config: DokkenConfig,
    llm_client: LLMClient,
) -> str:
    """
    Generate initial architectural documentation (descriptive).

    Steps:
    1. Analyze codebase
    2. LLM extracts architectural essence
    3. Format as markdown
    4. Save to ARCHITECTURE.md
    5. Prompt user to refine manually

    Returns:
        Generated markdown content
    """

    # Step 1: Analyze code
    code_context = analyze_code_context(
        path=module_path,
        file_types=config.file_types,
        exclusions=config.exclusions,
        depth=config.file_depth,
    )

    # Step 2: Build prompt
    prompt = build_architectural_extraction_prompt(
        code_context=code_context,
        custom_prompts=config.custom_prompts,
    )

    # Step 3: Generate markdown (free-form, no schema)
    # Note: Returns plain text, not structured output
    architectural_docs = await llm_client.generate_text(
        prompt=prompt,
        temperature=0.0,
    )

    # Step 4: Save to ARCHITECTURE.md
    output_filename = config.architectural_docs.output_filename or "ARCHITECTURE.md"
    output_path = module_path / output_filename
    output_path.write_text(architectural_docs)

    # Step 5: Prompt user to refine
    console.print("\n[green]✓ Generated ARCHITECTURE.md[/green]")
    console.print("\n[yellow]Next steps:[/yellow]")
    console.print("1. Review ARCHITECTURE.md")
    console.print("2. Change descriptive language → prescriptive (MUST, MUST NOT)")
    console.print("3. Add constraints not evident from code")
    console.print("4. Remove implementation details")
    console.print("5. Configure enforcement in .dokken.toml")
    console.print(f"6. Run: dokken check {module_path} --arch-docs")

    return architectural_docs
```

### Check Architectural Compliance Workflow

```python
async def check_architectural_compliance(
    module_path: Path,
    config: DokkenConfig,
    llm_client: LLMClient,
    dry_run: bool = False,
) -> ArchitecturalComplianceCheck:
    """
    Check if code complies with architectural documentation.

    Steps:
    1. Load ARCHITECTURE.md
    2. Analyze current codebase
    3. Check for violations in configured sections
    4. Report violations (fail build if severity=blocking)

    Args:
        dry_run: If True, show what would be checked without failing
    """

    # Step 1: Load architectural documentation
    output_filename = config.architectural_docs.output_filename or "ARCHITECTURE.md"
    arch_docs_path = module_path / output_filename

    if not arch_docs_path.exists():
        raise FileNotFoundError(
            f"No architectural documentation found at {arch_docs_path}. "
            f"Run 'dokken generate {module_path} --arch-docs' first."
        )

    architectural_docs = arch_docs_path.read_text()

    # Step 2: Analyze current code
    code_context = analyze_code_context(
        path=module_path,
        file_types=config.file_types,
        exclusions=config.exclusions,
        depth=config.file_depth,
    )

    # Step 3: Determine which sections to check
    sections_to_check = _extract_sections_to_check(
        architectural_docs=architectural_docs,
        config=config.architectural_docs,
    )

    # Step 4: Build compliance check prompt
    prompt = build_architectural_compliance_prompt(
        code_context=code_context,
        architectural_docs=architectural_docs,
        sections_to_check=sections_to_check,
        custom_prompts=config.custom_prompts,
    )

    # Step 5: Check compliance
    compliance = await llm_client.generate_structured_output(
        prompt=prompt,
        output_model=ArchitecturalComplianceCheck,
    )

    # Step 6: Handle result
    if dry_run:
        _print_dry_run_report(compliance, sections_to_check)
        return compliance

    if not compliance.compliant:
        severity = config.architectural_docs.severity
        if severity == "blocking":
            raise ArchitecturalComplianceError(
                f"Architectural violations detected in {module_path}:\n"
                + format_violations_report(compliance.violations)
            )
        elif severity == "warning":
            console.print(f"[yellow]⚠ Architectural warnings in {module_path}[/yellow]")
            console.print(format_violations_report(compliance.violations))
        else:  # advisory
            console.print(f"[blue]ℹ Architectural suggestions for {module_path}[/blue]")
            console.print(format_violations_report(compliance.violations))

    return compliance


def _extract_sections_to_check(
    architectural_docs: str,
    config: ArchitecturalDocsConfig,
) -> list[str]:
    """
    Extract section names from ARCHITECTURE.md based on config.

    Returns list of section names to check.
    """
    # Parse markdown to find all section headings
    all_sections = _parse_markdown_sections(architectural_docs)

    # Filter based on config
    if config.sections == ["*"]:
        # Check all sections except skipped ones
        return [
            s for s in all_sections
            if not any(skip in s for skip in config.skip_sections)
        ]
    else:
        # Check only configured sections
        return [
            s for s in all_sections
            if s in config.sections
        ]


def _parse_markdown_sections(markdown: str) -> list[str]:
    """Parse markdown and extract section headings (## Level 2 headings)."""
    import re
    # Match ## Heading (but not ### or #)
    pattern = r"^## (.+)$"
    matches = re.findall(pattern, markdown, re.MULTILINE)
    return [m.strip() for m in matches]
```

______________________________________________________________________

## Output Format

### ARCHITECTURE.md Structure (Generated - Phase 1)

````markdown
# Architecture: Payment Service

## Overview

The payment service handles payment processing, order fulfillment,
and ledger management. It communicates with external payment processors
and maintains transactional consistency.

## Layering

The codebase uses a three-layer architecture:
- **API Layer** (`api/`) - FastAPI routes and HTTP handling
- **Domain Layer** (`domain/`) - Business logic and orchestration
- **Data Layer** (`data/`) - Database access via SQLAlchemy

The domain layer imports from the data layer for persistence operations.

## Data Flow

Payment requests flow from API → Domain → Data. The domain layer
orchestrates transactions across Payment and Ledger tables.

## External Dependencies

- Stripe API for payment processing (via `stripe` library)
- PostgreSQL database (via SQLAlchemy ORM)
- Redis for caching (via `redis-py`)

## Patterns

The codebase uses the Repository pattern for database access.
Most domain operations use repositories, though some direct
ORM usage exists in newer code.

## Diagram

```mermaid
graph TD
    API[API Layer] --> Domain[Domain Layer]
    Domain --> Data[Data Layer]
    Domain --> Stripe[Stripe API]
    Data --> DB[(PostgreSQL)]
````

````

### ARCHITECTURE.md Structure (Refined - Phase 2)

```markdown
# Architecture: Payment Service

## Overview

The payment service handles payment processing with strict
transactional guarantees and well-defined architectural boundaries.

## Layering

The system MUST maintain three distinct layers:

- **API Layer** (`api/`) - HTTP handling ONLY. No business logic.
- **Domain Layer** (`domain/`) - Business logic and orchestration.
- **Data Layer** (`data/`) - Database access via Repository pattern.

**Constraints:**
- Domain layer MUST NOT import from API layer
- Domain layer MUST NOT import from Data layer (use dependency injection)
- API layer MUST only call Domain layer, never Data layer directly

## Transaction Boundaries

All payment operations MUST be atomic:
- Any operation touching both Payment and Ledger tables MUST run in a single transaction
- Commits MUST happen after all validation passes
- Rollback MUST occur on any failure

## External Service Communication

All communication with Stripe MUST go through the `PaymentGateway` abstraction:
- Direct usage of `stripe` library is FORBIDDEN outside `gateway/stripe_gateway.py`
- New payment providers MUST implement `PaymentGateway` interface
- Domain layer MUST depend on `PaymentGateway` interface, not concrete implementations

## Data Access Patterns

All database access MUST use the Repository pattern:
- Direct SQLAlchemy ORM usage is FORBIDDEN outside `data/repositories/`
- Domain layer MUST receive repository instances via dependency injection
- Repositories MUST return domain models, not ORM entities

## Diagram

```mermaid
graph TD
    API[API Layer] -->|allowed| Domain[Domain Layer]
    Domain -->|allowed via DI| Gateway[Payment Gateway]
    Domain -->|allowed via DI| Repo[Repositories]
    Repo --> Data[Data Layer]
    Gateway --> Stripe[Stripe API]
    Data --> DB[(PostgreSQL)]

    Domain -.forbidden.-> Data
    Domain -.forbidden.-> Stripe
    API -.forbidden.-> Data
````

```

### Violation Report Output

When violations are detected:

```

❌ Architectural Compliance Check Failed

Module: src/payment
Violations: 3
Sections checked: Layering, Transaction Boundaries, Data Access Patterns

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Section: Layering
Severity: blocking

Constraint: Domain layer MUST NOT import from Data layer

Violation:
The domain layer directly imports Repository classes from the data
layer, violating the dependency inversion principle. Domain should
receive repositories via dependency injection.

Files:
• src/domain/payment_service.py:5
• src/domain/order_service.py:3

Suggested Fix:
Remove direct imports of repositories. Instead, accept repository
instances as constructor parameters in service classes. Use a
dependency injection container to wire dependencies.

Code:
src/domain/payment_service.py:
3 | from src.domain.models import Payment
4 | from src.domain.events import PaymentProcessed

> 5 | from src.data.repositories import PaymentRepository # ← VIOLATION
> 6 |
> 7 | class PaymentService:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Section: External Service Communication
Severity: blocking

Constraint: Direct usage of stripe library is FORBIDDEN outside gateway/stripe_gateway.py

Violation:
New refund functionality directly uses the stripe library instead of
going through the PaymentGateway abstraction.

Files:
• src/domain/refund_service.py:23

Suggested Fix:
Add a `process_refund()` method to the PaymentGateway interface and
implement it in StripeGateway. Update RefundService to use the gateway
instead of direct stripe calls.

Code:
src/domain/refund_service.py:
21 | def process_refund(self, payment_id: str, amount: Decimal):
22 | payment = self.payment_repo.get(payment_id)

> 23 | stripe.Refund.create(charge=payment.stripe_id, amount=amount) # ← VIOLATION
> 24 | self.payment_repo.mark_refunded(payment_id)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Section: Data Access Patterns
Severity: blocking

Constraint: Direct SQLAlchemy ORM usage is FORBIDDEN outside data/repositories/

Violation:
API route directly queries database using SQLAlchemy instead of using
a repository.

Files:
• src/api/routes/stats.py:18

Suggested Fix:
Create a StatsRepository with a method for fetching payment statistics.
Update the route handler to use the repository instead of direct queries.

Code:
src/api/routes/stats.py:
16 | @router.get("/stats")
17 | def get_stats(session: Session = Depends(get_session)):

> 18 | return session.query(Payment).filter(...).all() # ← VIOLATION
> 19 |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary:
✗ 3 blocking violations must be fixed before merge

- Layering: 2 violations
- External Service Communication: 1 violation
- Data Access Patterns: 1 violation

To fix these violations, update code to comply with ARCHITECTURE.md
or update ARCHITECTURE.md if constraints should change.

```

---

## Implementation Phases

### Phase 1: Core Infrastructure (2-3 weeks)

**Goal:** Basic architectural docs generation and checking

**Tasks:**

1. **Data Models**
   - Add `ArchitecturalViolation` model
   - Add `ArchitecturalComplianceCheck` model
   - Add `ArchitecturalDocsConfig` to configuration models

2. **LLM Prompts**
   - Implement `ARCHITECTURAL_EXTRACTION_PROMPT`
   - Implement `ARCHITECTURAL_COMPLIANCE_CHECK_PROMPT`

3. **CLI Commands**
   - Add `--arch-docs` flag to `generate` command
   - Add `--arch-docs` flag to `check` command
   - Add `--dry-run` flag for compliance checking

4. **Basic Workflows**
   - Implement `generate_architectural_docs()`
   - Implement `check_architectural_compliance()`
   - Implement `_extract_sections_to_check()`
   - Implement `_parse_markdown_sections()`

5. **Configuration Loading**
   - Add `[architectural_docs]` section to TOML schema
   - Support `sections`, `severity`, `skip_sections` config
   - Support per-module overrides

**Deliverable:**
- `dokken generate <module> --arch-docs` creates ARCHITECTURE.md
- `dokken check <module> --arch-docs` detects violations

**Tests:**
- Test architectural docs generation
- Test section parsing from markdown
- Test compliance checking with mock violations
- Test configuration loading

---

### Phase 2: Output Formatting & Reporting (1 week)

**Goal:** Clear, actionable violation reports

**Tasks:**

1. **Violation Reporter**
   - Implement `format_violations_report()` in `src/output/formatters.py`
   - Group violations by section
   - Color-coded output (red=blocking, yellow=warning, blue=advisory)
   - Code excerpts with line numbers
   - Summary statistics

2. **Dry Run Mode**
   - Implement `_print_dry_run_report()`
   - Show which sections would be checked
   - Preview violations without failing

3. **Error Messages**
   - Add `ArchitecturalComplianceError` exception
   - Helpful error messages with next steps
   - Suggest fixes in error output

**Deliverable:**
- Clear, actionable violation reports
- `--dry-run` mode for testing

**Tests:**
- Test report formatting
- Test dry-run mode
- Test error messages

---

### Phase 3: Multi-Module Support (1 week)

**Goal:** Check multiple modules in CI

**Tasks:**

1. **Multi-Module Checking**
   - Extend `check_multiple_modules_drift()` to support `--arch-docs`
   - Aggregate violations across modules
   - Report per-module compliance

2. **Severity Handling**
   - Respect per-module severity overrides
   - Allow mixing blocking/warning/advisory across modules
   - Fail build only if any module has blocking violations

3. **Configuration Validation**
   - Validate `sections` reference existing sections
   - Warn if configured sections don't exist in ARCHITECTURE.md
   - Validate severity levels

**Deliverable:**
- `dokken check --all --arch-docs` checks all modules
- Per-module severity configuration

**Tests:**
- Test multi-module checking
- Test severity overrides
- Test configuration validation

---

### Phase 4: Caching & Performance (1 week)

**Goal:** Fast compliance checks via caching

**Tasks:**

1. **Cache Key Generation**
   - Generate cache keys from (code_context_hash + arch_docs_hash)
   - Separate cache namespace for architectural docs

2. **Compliance Result Caching**
   - Cache compliant results (no violations)
   - Invalidate cache when code or ARCHITECTURE.md changes
   - Cache per-section results for partial invalidation

3. **Performance Optimization**
   - Benchmark compliance check performance
   - Optimize section extraction and parsing
   - Parallel checking of multiple sections if possible

**Deliverable:**
- Fast repeated compliance checks (<2s for cached results)

**Tests:**
- Test cache hit/miss behavior
- Test cache invalidation
- Benchmark performance

---

### Phase 5: Polish & Documentation (1 week)

**Goal:** Production-ready feature

**Tasks:**

1. **User Documentation**
   - Add architectural docs section to README
   - Create example ARCHITECTURE.md files
   - Document best practices for refining docs
   - Update CLAUDE.md with architectural docs workflow

2. **Error Handling**
   - Handle malformed ARCHITECTURE.md gracefully
   - Handle missing sections
   - Handle LLM errors

3. **User Feedback**
   - Improve prompts based on testing
   - Refine violation messages
   - Add helpful hints to output

**Deliverable:**
- Complete user documentation
- Robust error handling

**Tests:**
- Test error cases
- Integration tests end-to-end

---

## Integration Points

### Integration with Existing Systems

1. **Configuration System**
   - Add `architectural_docs` section to `DokkenConfig`
   - Extend `.dokken.toml` schema
   - Support per-module overrides

2. **CLI Commands**
   - Add `--arch-docs` flag alongside existing flags
   - Share code analyzer, LLM client
   - Preserve backward compatibility

3. **LLM Client**
   - Reuse existing `LLMClient` class
   - Add new method: `generate_text()` for free-form markdown
   - Use existing `generate_structured_output()` for compliance checks

4. **Cache System**
   - Extend cache to support architectural docs
   - Separate cache namespace (`arch-docs:`) to avoid collisions

5. **Error Handling**
   - Add new exception: `ArchitecturalComplianceError`
   - Set exit code 2 for architectural violations (vs 1 for drift)

6. **Multi-Module Workflow**
   - Extend `check_multiple_modules_drift()` to handle `--arch-docs`
   - Aggregate results across modules

---

## Avoiding AST Linter Overlap

### What We DON'T Check

We explicitly avoid checks that AST-based linters can handle better:

**Ruff/Flake8/Pylint already check:**
- Import statements (unused, ordering, grouping)
- Cyclomatic complexity
- Naming conventions
- Code style and formatting
- Type annotations
- Common code smells

**What we DO check:**
- High-level architectural patterns (e.g., "all DB access via repositories")
- Layer boundary violations (requires understanding intent, not just imports)
- Abstraction violations (e.g., "bypass gateway abstraction")
- Transaction boundaries (requires semantic understanding)
- Architectural invariants (e.g., "authentication only in auth module")

**Example Distinction:**

❌ **Bad (AST can check):**
```

Rule: "Do not import from ui module"
This is just an import pattern - use Ruff with banned-imports

```

✅ **Good (Requires LLM):**
```

Rule: "Domain layer must not depend on infrastructure layer.
Use dependency injection to invert dependencies."

This requires understanding:

- What constitutes "domain" vs "infrastructure"
- Whether dependency injection is properly used
- Whether the architectural intent is preserved

````

### Prompt Instructions to Avoid Overlap

We include this in compliance check prompt:

```python
AVOID_AST_OVERLAP_INSTRUCTIONS = """
Focus ONLY on architectural violations that require semantic understanding:

✅ Check:
- Layer/boundary violations (requires understanding layer boundaries)
- Pattern violations (requires recognizing architectural patterns)
- Abstraction bypasses (requires understanding what abstraction provides)
- Transaction boundary violations (requires understanding transactional semantics)

❌ Do NOT check (leave to AST linters):
- Import statements of forbidden modules (use ruff/flake8 with banned-imports)
- Cyclomatic complexity (use ruff with mccabe)
- Naming conventions (use ruff/pylint)
- Type annotations (use mypy/pyright)
- Code formatting (use ruff format/black)

If a constraint can be expressed as a simple pattern match or AST rule,
do NOT flag it. Only flag violations that require understanding
architectural intent and relationships.
"""
````

______________________________________________________________________

## Testing Strategy

### Unit Tests

- **Section Parsing**: Test extracting sections from markdown
- **Configuration**: Test TOML parsing, validation, overrides
- **Violation Models**: Test Pydantic validation

### Integration Tests

```python
def test_generate_architectural_docs(tmp_path, mock_llm):
    """Test generating initial ARCHITECTURE.md."""
    module_path = tmp_path / "src"
    module_path.mkdir()
    (module_path / "api.py").write_text("# API code")
    (module_path / "domain.py").write_text("# Domain code")

    result = generate_architectural_docs(
        module_path=module_path,
        config=default_config(),
        llm_client=mock_llm,
    )

    arch_docs = (module_path / "ARCHITECTURE.md").read_text()
    assert "## Layering" in arch_docs  # Contains sections
    assert "must" not in arch_docs.lower()  # Descriptive, not prescriptive


def test_check_compliance_with_violations(tmp_path, mock_llm):
    """Test detecting architectural violations."""
    module_path = tmp_path / "src"
    module_path.mkdir()

    # Create ARCHITECTURE.md with prescriptive constraint
    (module_path / "ARCHITECTURE.md").write_text("""
# Architecture

## Layering
Domain layer MUST NOT import from data layer.
Use dependency injection instead.
    """)

    # Create code that violates constraint
    (module_path / "domain.py").write_text(
        "from data.repositories import UserRepo"
    )

    with pytest.raises(ArchitecturalComplianceError) as exc:
        check_architectural_compliance(
            module_path=module_path,
            config=default_config(),
            llm_client=mock_llm,
        )

    assert "Layering" in str(exc.value)
    assert "domain.py" in str(exc.value)


def test_check_compliance_passes(tmp_path, mock_llm):
    """Test compliant code passes check."""
    module_path = tmp_path / "src"
    module_path.mkdir()

    (module_path / "ARCHITECTURE.md").write_text("""
# Architecture

## Layering
Domain layer MUST NOT import from data layer.
    """)

    (module_path / "domain.py").write_text(
        "from domain.models import User"  # OK - within same layer
    )

    result = check_architectural_compliance(
        module_path=module_path,
        config=default_config(),
        llm_client=mock_llm,
    )

    assert result.compliant
    assert len(result.violations) == 0


def test_section_filtering(tmp_path, mock_llm):
    """Test checking only configured sections."""
    module_path = tmp_path / "src"
    module_path.mkdir()

    (module_path / "ARCHITECTURE.md").write_text("""
# Architecture

## Layering
Domain MUST NOT import from data.

## Future Plans
We plan to add caching later.
    """)

    config = default_config()
    config.architectural_docs.sections = ["Layering"]  # Only check Layering
    config.architectural_docs.skip_sections = ["Future Plans"]

    result = check_architectural_compliance(
        module_path=module_path,
        config=config,
        llm_client=mock_llm,
    )

    assert "Future Plans" not in result.sections_checked
    assert "Layering" in result.sections_checked
```

### Regression Tests

- **Backward Compatibility**: Existing `generate`/`check` unchanged
- **Configuration**: Old `.dokken.toml` files still parse
- **Caching**: Architectural docs don't break existing cache

______________________________________________________________________

## Migration Path

### For Existing Dokken Users

**Opt-in Feature:** Architectural documentation is completely optional.

**Gradual Adoption:**

```bash
# Step 1: Continue using existing tech docs
dokken check --all

# Step 2: Generate architectural docs for one module
dokken generate src/core --arch-docs

# Step 3: Review and refine ARCHITECTURE.md manually
# (change descriptive → prescriptive, add constraints)

# Step 4: Configure enforcement (warning mode first)
# .dokken.toml:
# [modules.src_core.architectural_docs]
# severity = "warning"

# Step 5: Test in CI (warnings only, doesn't fail build)
dokken check src/core --arch-docs

# Step 6: Fix violations, then switch to blocking
# [modules.src_core.architectural_docs]
# severity = "blocking"

# Step 7: Expand to more modules gradually
```

### For New Users

**Recommended Workflow:**

1. Start with tech docs: `dokken generate src`
1. Once architecture stabilizes, add architectural docs: `dokken generate src --arch-docs`
1. Refine ARCHITECTURE.md to be prescriptive
1. Enforce in CI: `dokken check --all --arch-docs`

______________________________________________________________________

## Open Questions

### Design Decisions Needed

1. **Should we support sub-sections?**

   - Allow checking specific sub-sections (### Level 3 headings)?
   - Or only top-level sections (## Level 2 headings)?

1. **How to handle rule evolution?**

   - When ARCHITECTURE.md changes, how to handle existing violations?
   - Support "grandfathering" existing violations temporarily?

1. **Should we support inline exceptions?**

   - Allow code comments like `# arch-docs: ignore-section Layering`?
   - Or force all exceptions to be documented in ARCHITECTURE.md?

1. **How to compose rules across modules?**

   - Support repo-level ARCHITECTURE.md + module-level?
   - How do they merge/override?

1. **Should we provide ARCHITECTURE.md templates?**

   - Pre-built templates for common architectures (clean, hexagonal, etc.)?
   - Risk: Encourages copy-paste instead of thoughtful architecture

1. **Mermaid diagram enforcement?**

   - Should we parse and validate Mermaid diagrams?
   - Or treat them as documentation-only?

______________________________________________________________________

## Success Metrics

### Technical Metrics

- **Violation Detection Accuracy**: >85% precision (few false positives)
- **Performance**: Compliance check \<5s for 10k LOC module (with caching)
- **Cache Hit Rate**: >70% for unchanged code/docs

### User Metrics

- **Adoption**: % of modules with ARCHITECTURE.md
- **CI Integration**: % of projects using `--arch-docs` in CI
- **Refinement Rate**: % of generated docs that get manually refined

### Quality Metrics

- **Architecture Stability**: ARCHITECTURE.md changes infrequently (\<1x/month)
- **Violation Prevention**: Reduction in architectural violations over time

______________________________________________________________________

## Future Enhancements

### Potential Follow-ups

1. **Interactive Refinement Assistant**

   - Help user refine generated docs interactively
   - Suggest prescriptive language transformations

1. **Architecture Templates**

   - Pre-built templates for common patterns (carefully designed)
   - Customizable starting points

1. **Visual Diagram Validation**

   - Parse Mermaid diagrams
   - Validate code matches diagram structure

1. **Architecture Evolution Tracking**

   - Track how architecture changes over time
   - Visualize architectural drift trends

1. **Multi-Repo Architectural Constraints**

   - Share architectural rules across microservices
   - Enforce cross-service boundaries

1. **Custom Violation Severity**

   - Per-section severity overrides
   - Different enforcement levels for different constraints

______________________________________________________________________

## Conclusion

This implementation plan provides a flexible, user-driven approach to architectural documentation that:

**Leverages LLM strengths:**

- Extract high-level architectural essence from code
- Interpret free-form architectural constraints
- Detect semantic violations (not just syntax)

**Avoids LLM weaknesses:**

- No prescriptive rule schemas
- No predefined architecture categories
- User refines generated docs (LLM as assistant, not decision-maker)

**Complements existing tools:**

- Focuses on architecture, not implementation
- Avoids overlap with AST linters
- Integrates with existing dokken workflows

**Empowers users:**

- User defines architectural sections
- User decides what to enforce
- User refines generated docs
- Flexible configuration per module

The three-phase workflow (Generate → Refine → Enforce) ensures that architectural documentation starts from reality (code) but converges to intent (user-refined constraints), creating a living architectural governance system.
