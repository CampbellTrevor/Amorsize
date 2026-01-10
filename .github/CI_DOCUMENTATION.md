# CI/CD Infrastructure Documentation

## Overview

Amorsize uses GitHub Actions for continuous integration and deployment. This ensures code quality, cross-platform compatibility, and automated releases.

## Workflows

### 1. CI Workflow (`ci.yml`)

**Triggers:**
- Push to `main`, `Iterate`, or `develop` branches
- Pull requests to these branches
- Manual dispatch

**Jobs:**

#### Test Matrix
- **Platforms**: Ubuntu, macOS, Windows
- **Python Versions**: 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- **Total Combinations**: 20 (excluding Python 3.7 on macOS ARM64)

**What it does:**
- Installs package with dev and full dependencies
- Runs complete test suite (630+ tests)
- Validates package imports

#### Coverage Analysis
- **Platform**: Ubuntu only
- **Python**: 3.11
- Generates coverage reports
- Uploads to Codecov (optional)

#### Package Build
- **Platform**: Ubuntu
- **Python**: 3.11
- Builds wheel and source distribution
- Validates package with `twine check`
- Tests wheel installation
- Uploads build artifacts

#### Code Quality
- **Platform**: Ubuntu
- **Python**: 3.11
- Runs flake8 for syntax errors and code quality
- Non-blocking (continues on error)

### 2. Security Workflow (`security.yml`)

**Triggers:**
- Push to `main` or `Iterate` branches
- Pull requests
- Weekly schedule (Monday 6:00 AM UTC)
- Manual dispatch

**Jobs:**

#### CodeQL Analysis
- Advanced security scanning
- Queries: security-and-quality
- Language: Python
- Uploads results to GitHub Security tab

#### Dependency Review
- **PR Only**: Checks dependency changes
- Fails on moderate+ severity vulnerabilities
- Prevents vulnerable dependencies from being added

#### Safety Check
- Scans installed packages for known vulnerabilities
- Non-blocking (continues on error)
- JSON output for programmatic parsing

### 3. PR Checks Workflow (`pr-checks.yml`)

**Triggers:**
- Pull request events (opened, edited, synchronize, reopened)

**Jobs:**

#### PR Title Validation
- Enforces conventional commit format
- Allowed types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
- Scope optional
- Non-blocking

#### Change Validation
- Runs quick subset of tests (optimizer and system_info)
- Checks if test files were modified
- Provides fast feedback on PRs

### 4. Scheduled Tests Workflow (`scheduled.yml`)

**Triggers:**
- Weekly schedule (Monday 9:00 AM UTC)
- Manual dispatch

**Jobs:**

#### Comprehensive Testing
- **Matrix**: Ubuntu, macOS, Windows × Python 3.8, 3.11, 3.13
- Runs full test suite with long traceback
- Tests basic example script
- Runs system validation
- Non-blocking for examples

#### Dependency Validation
- **Platform**: Ubuntu
- Tests minimal installation (no optional deps)
- Tests full installation (with psutil)
- Ensures both configurations work

### 5. Release Workflow (`release.yml`)

**Triggers:**
- GitHub release published
- Manual dispatch (with Test PyPI option)

**Jobs:**

#### Build and Publish
- Builds wheel and source distribution
- Validates package
- Tests installation
- Publishes to PyPI (on release) or Test PyPI (manual)
- Requires secrets: `PYPI_API_TOKEN` or `TEST_PYPI_API_TOKEN`

## Status Badges

The README displays real-time status:

```markdown
[![CI](https://github.com/CampbellTrevor/Amorsize/workflows/CI/badge.svg)](...)
[![Security](https://github.com/CampbellTrevor/Amorsize/workflows/Security/badge.svg)](...)
```

## Secrets Configuration

Required secrets (configured in repository settings):

- `PYPI_API_TOKEN`: PyPI authentication token for releases
- `TEST_PYPI_API_TOKEN`: Test PyPI token for pre-release testing
- `CODECOV_TOKEN`: (Optional) For code coverage tracking

## Local Testing

Before pushing, run locally:

```bash
# Install dev dependencies
pip install -e ".[dev,full]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=amorsize --cov-report=term

# Build package
python -m build

# Check package
twine check dist/*
```

## Workflow Optimization

- **Fail-fast disabled**: Tests continue even if one configuration fails
- **Artifacts uploaded**: Build artifacts saved for 90 days (default)
- **Caching**: pip cache is automatically handled by setup-python action
- **Parallel execution**: Jobs run concurrently when possible

## Maintenance

### Adding Python Version
1. Update matrix in `ci.yml`
2. Update matrix in `scheduled.yml`
3. Update `pyproject.toml` classifiers
4. Update README.md badge

### Updating Dependencies
1. Dependencies are specified in `pyproject.toml`
2. CI automatically tests with latest compatible versions
3. Use `pip list` in CI logs to see actual versions used

### Debugging Failures
1. Check workflow logs in GitHub Actions tab
2. Look for specific job that failed
3. Review step-by-step output
4. Test locally with same Python version/OS if possible
5. Use `workflow_dispatch` to manually trigger workflows for testing

## Best Practices

1. **Always run tests locally first**
2. **Keep workflows fast**: Use matrix testing efficiently
3. **Don't block on non-critical checks**: Use `continue-on-error`
4. **Monitor scheduled runs**: Check weekly test results
5. **Keep secrets secure**: Never log or expose tokens
6. **Update actions regularly**: Use dependabot or manual updates

## Future Enhancements

Potential improvements:
- Add performance benchmarking workflow
- Integrate mutation testing
- Add auto-changelog generation
- Set up automatic dependency updates
- Add code complexity analysis
- Create deployment preview environments
