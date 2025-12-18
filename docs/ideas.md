# Ideas for future development

## Human-in-the-loop

In order to capture _intent_ in the documentation, we need to involve a human. AI can never infer that alone. We should
add a short questionaire, with questions like:

- What problems does this module solve?
- What are the module's core responsibilities?
- What is not this module's responsibility?
- How does the module fit into the larger system?
- What are the main entry points in the module?
- What are the important invariants, assumptions, or contracts?
- What are the module's known limitations?
- What are common pitfalls for contributors?

## Some way to exclude/deny changes permanently

Sometimes, you don't want the things dokken suggests.

## Enable automatic git branches

Controlled by command line param, you could create a branch with the documentation changes needed automatically, instead
of committing to the current branch.
