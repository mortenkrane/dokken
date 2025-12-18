# Releasing to PyPI

This guide explains how to release new versions of Dokken to PyPI using the automated release-please workflow.

## Overview

Dokken uses [release-please](https://github.com/googleapis/release-please) to automate versioning, changelog generation, and PyPI publishing. The entire process is driven by conventional commits and requires minimal manual intervention.

## One-Time Setup

### 1. Configure PyPI Trusted Publishing

Before the first release, you must set up trusted publishing on PyPI:

1. **Create the project on PyPI** (if not already done):
   - Go to https://pypi.org/
   - Create a new project named `dokken` (or claim it if you're the owner)

2. **Set up Trusted Publishing**:
   - Go to https://pypi.org/manage/account/publishing/
   - Click "Add a new publisher"
   - Fill in the form:
     - **PyPI Project Name**: `dokken`
     - **Owner**: `mortenkrane`
     - **Repository**: `dokken`
     - **Workflow name**: `publish-pypi.yml`
     - **Environment name**: (leave blank)
   - Click "Add"

3. **Verify the configuration**:
   - The trusted publisher should appear in your list
   - No API tokens or secrets are needed - GitHub Actions will authenticate automatically

### 2. Understand Conventional Commits

All commits to the `main` branch should follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` - New features (bumps **minor** version: 0.1.0 → 0.2.0)
- `fix:` - Bug fixes (bumps **patch** version: 0.1.0 → 0.1.1)
- `feat!:` or `BREAKING CHANGE:` - Breaking changes (bumps **major** version: 0.1.0 → 1.0.0)
- `docs:` - Documentation changes (appears in changelog, no version bump)
- `refactor:` - Code refactoring (appears in changelog, no version bump)
- `perf:` - Performance improvements (appears in changelog, no version bump)
- `test:` - Test changes (hidden from changelog, no version bump)
- `chore:` - Maintenance tasks (hidden from changelog, no version bump)
- `ci:` - CI/CD changes (hidden from changelog, no version bump)

**Examples:**
```bash
git commit -m "feat: add support for markdown export"
git commit -m "fix: correct drift detection logic"
git commit -m "docs: update API documentation"
git commit -m "feat!: remove deprecated --legacy flag"
```

## Release Workflow

### Step 1: Develop and Commit

1. **Make your changes** on a feature branch
2. **Merge to main** using conventional commit

### Step 2: Release-Please Creates PR

After pushing to `main`, the release-please GitHub Action will:

1. **Analyze commits** since the last release
2. **Calculate new version** based on commit types
3. **Create or update a release PR** with:
   - Updated version in `pyproject.toml`
   - Generated/updated `CHANGELOG.md`
   - A clear title like "chore(main): release 0.2.0"

**What the release PR looks like:**
- Title: `chore(main): release 0.2.0`
- Description: Summary of changes organized by type
- Files changed: `pyproject.toml`, `CHANGELOG.md`, `.release-please-manifest.json`

### Step 3: Review and Merge Release PR

1. **Review the release PR**:
   - Check the version number is correct
   - Review the changelog entries
   - Verify all changes are included

2. **Merge the release PR**:
   - Click "Merge pull request"
   - The release-please workflow will automatically:
     - Create a GitHub release tagged with the version (e.g., `v0.2.0`)
     - Build the package (wheel + sdist)
     - Attach the built artifacts to the GitHub release

### Step 4: Automatic PyPI Publishing

When the GitHub release is created:

1. **The publish-pypi workflow triggers automatically**
2. **Package is built** using `uv build`
3. **Package is published to PyPI** using trusted publishing
4. **Verify the release** at https://pypi.org/project/dokken/

## Version Bumping Rules

Release-please follows semantic versioning:

| Commit Type | Version Change | Example |
|-------------|----------------|---------|
| `fix:` | Patch (0.1.0 → 0.1.1) | Bug fixes |
| `feat:` | Minor (0.1.0 → 0.2.0) | New features |
| `feat!:` or `BREAKING CHANGE:` | Major (0.1.0 → 1.0.0) | Breaking changes |
| `docs:`, `refactor:`, `perf:` | No bump (appears in changelog) | Non-breaking improvements |
| `test:`, `chore:`, `ci:` | No bump (hidden from changelog) | Internal changes |

**Special cases:**
- Multiple commit types: Uses the highest precedence (breaking > feat > fix)
- No releasable commits: No release PR is created
- Pre-1.0.0 versions: `feat:` bumps minor, `fix:` bumps patch (configured in `release-please-config.json`)

## Troubleshooting

### Release PR Not Created

**Possible causes:**
- No conventional commits since last release
- Only `chore:`, `test:`, or `ci:` commits (these don't trigger releases)
- Commits don't follow conventional commit format

**Solution:**
- Check your commit messages in the GitHub UI
- Ensure at least one commit is `feat:`, `fix:`, `docs:`, `refactor:`, or `perf:`

### PyPI Publishing Failed

**Possible causes:**
- Trusted publishing not configured correctly
- Package name already exists and you're not the owner
- Version already published to PyPI

**Solution:**
1. Check the GitHub Actions logs in the "Actions" tab
2. Verify trusted publishing settings on PyPI
3. If version exists, merge more commits and create a new release

### Version Not Updated Correctly

**Possible causes:**
- Conventional commit format not followed
- Wrong commit type used (e.g., `chore:` instead of `feat:`)

**Solution:**
- Review the release-please PR to see what it detected
- If incorrect, close the PR, fix commits on main, and push again
- Release-please will update the PR automatically

## Manual Release (Emergency Only)

If you need to manually release (not recommended):

1. **Update version** in `pyproject.toml` and `.release-please-manifest.json`
2. **Build package**:
   ```bash
   uv build
   ```
3. **Create GitHub release** manually with the tag `v{version}`
4. **Upload artifacts** to the release
5. **PyPI publishing** will trigger automatically from the release event

## Files and Configuration

### Configuration Files

- `release-please-config.json` - Release-please configuration
- `.release-please-manifest.json` - Current version tracking
- `.github/workflows/release-please.yml` - Release automation workflow
- `.github/workflows/publish-pypi.yml` - PyPI publishing workflow

### Key Settings

From `release-please-config.json`:
- **release-type**: `python` (updates `pyproject.toml`)
- **package-name**: `dokken`
- **bump-minor-pre-major**: `true` (pre-1.0 versions bump minor for features)
- **changelog-sections**: Which commit types appear in changelog

## Best Practices

1. **Always use conventional commits** on main branch
2. **Batch related changes** into a single commit when possible
3. **Test before merging** to main (CI should pass)
4. **Review release PRs** carefully before merging
5. **Document breaking changes** in commit messages:
   ```bash
   git commit -m "feat!: change API response format

   BREAKING CHANGE: The API now returns JSON instead of XML.
   Update all clients to parse JSON responses."
   ```

## Example Full Release Cycle

```bash
# 1. Develop feature on branch
git checkout -b add-pdf-export
# ... make changes ...
pytest src/tests/ --cov=src
ruff format && ruff check

# 2. Commit with conventional commit
git commit -m "feat: add PDF export functionality"

# 3. Merge to main
git checkout main
git pull origin main
git merge add-pdf-export
git push origin main

# 4. Wait for release-please to create PR
# (Check GitHub "Pull Requests" tab)

# 5. Review and merge the release PR
# (Use GitHub UI)

# 6. Verify release
# - Check GitHub releases: https://github.com/mortenkrane/dokken/releases
# - Check PyPI: https://pypi.org/project/dokken/
```

## Additional Resources

- [Release Please Documentation](https://github.com/googleapis/release-please)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
