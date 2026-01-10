# GitHub Actions Workflows

This directory contains GitHub Actions workflows for continuous integration and deployment.

## Workflows

### CI Workflow (`ci.yml`)

Comprehensive continuous integration workflow that runs on every push and pull request.

**Jobs:**

1. **Test** - Multi-platform testing
   - Tests on Ubuntu, Windows, and macOS
   - Tests Python versions 3.7 through 3.13
   - Runs full test suite with pytest
   - Generates coverage reports (Ubuntu + Python 3.12)
   - Uploads coverage to Codecov

2. **Lint** - Code quality checks
   - Black (code formatting)
   - isort (import sorting)
   - flake8 (linting)
   - mypy (type checking)
   - All checks are non-blocking (continue-on-error: true)

3. **Build** - Package verification
   - Builds wheel and source distributions
   - Validates package with twine
   - Tests installation from wheel
   - Uploads build artifacts (retained for 7 days)

4. **Docs Check** - Documentation validation
   - Verifies README.md exists and has content
   - Checks for examples directory
   - Validates pyproject.toml metadata

5. **Status Check** - Overall CI status
   - Aggregates results from all jobs
   - Fails if any critical job fails
   - Provides clear pass/fail status

**Triggers:**
- Push to main, develop, or Iterate branches
- Pull requests to main, develop, or Iterate branches
- Manual workflow dispatch

**Features:**
- Matrix testing across platforms and Python versions
- Non-blocking linting (won't fail builds)
- Coverage reporting
- Build artifact preservation
- Clear status indicators

## Local Testing

Before pushing, you can test locally:

```bash
# Run tests
pytest -v

# Check formatting
black --check amorsize/ tests/

# Check imports
isort --check-only amorsize/ tests/

# Lint
flake8 amorsize/

# Type check
mypy amorsize/ --ignore-missing-imports

# Build package
python -m build
```

## Adding More Workflows

To add additional workflows:
1. Create a new `.yml` file in this directory
2. Define triggers, jobs, and steps
3. Reference existing workflows for patterns
4. Test locally before committing

## Secrets Required

- `CODECOV_TOKEN` (optional) - For uploading coverage reports to Codecov

If CODECOV_TOKEN is not set, coverage upload will be skipped but won't fail the build.
