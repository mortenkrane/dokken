# Dokken Examples

This directory contains complete example configurations and workflows for Dokken.

## Files

### `.dokken.toml`

Comprehensive configuration file demonstrating all available Dokken options:

- Module configuration for multi-module projects
- File type filters (Python, JavaScript, TypeScript, etc.)
- File depth configuration for code traversal
- Exclusion patterns for test files and boilerplate
- Custom prompts for LLM documentation generation
- Cache configuration for optimized CI/CD performance

**Usage:** Copy to your repository root as `.dokken.toml` and customize as needed.

### `dokken-drift-check.yml`

Complete GitHub Actions workflow for CI/CD integration:

- Automatic documentation drift detection on PRs and pushes
- Intelligent caching to minimize LLM API calls (80-95% token savings)
- Support for Anthropic/OpenAI/Google API keys
- Optional auto-fix job for automatic drift resolution
- Path-based triggers to only run when relevant files change

**Usage:** Copy to `.github/workflows/dokken-drift-check.yml` and configure your API key secret.

## Quick Start

1. **Configure your project:**

   ```bash
   cp examples/.dokken.toml .dokken.toml
   # Edit .dokken.toml to match your project structure
   ```

1. **Set up GitHub Actions:**

   ```bash
   cp examples/dokken-drift-check.yml .github/workflows/dokken-drift-check.yml
   # Add ANTHROPIC_API_KEY (or OPENAI_API_KEY/GOOGLE_API_KEY) to GitHub secrets
   ```

1. **Add cache to .gitignore:**

   ```bash
   echo ".dokken-cache.json" >> .gitignore
   ```

1. **Test locally:**

   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   dokken check --all
   ```

## Additional Resources

- [Main README](../README.md) - Complete Dokken documentation
- [Style Guide](../docs/style-guide.md) - Architecture and development conventions
- [Contributing Guide](../CONTRIBUTING.md) - Contribution guidelines

## Support

For questions or issues:

- GitHub Issues: <https://github.com/mortenkrane/dokken/issues>
- Documentation: <https://github.com/mortenkrane/dokken>
