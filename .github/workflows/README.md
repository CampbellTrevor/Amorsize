# GitHub Actions Workflows

This directory contains CI/CD workflows for the Amorsize project.

## Workflows

### CI Workflow (`ci.yml`)

**Triggers:**
- Push to `main`, `Iterate`, or `copilot/**` branches
- Pull requests to `main` or `Iterate` branches
- Manual workflow dispatch

**Jobs:**

#### 1. Test Job
Tests the package across multiple Python versions and operating systems.

**Test Matrix:**
- **Python Versions:** 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- **Operating Systems:** Ubuntu (Linux), macOS, Windows
- **Total Combinations:** 21 test configurations

**Steps:**
1. Checkout code
2. Set up Python with pip caching
3. Install package with dev and full dependencies
4. Run pytest with coverage
5. Upload coverage to Codecov (Ubuntu + Python 3.12 only)

**Coverage Reporting:**
- Coverage is collected for all test runs
- XML and terminal reports are generated
- Codecov upload happens only for Ubuntu + Python 3.12 to avoid redundant uploads

#### 2. Build Job
Validates that the package can be built and installed correctly.

**Steps:**
1. Checkout code
2. Set up Python 3.12
3. Install build tools (build, twine)
4. Build wheel and source distribution
5. Validate package metadata with twine
6. Test package installation
7. Verify imports work correctly
8. Upload build artifacts (retained for 30 days)

**Build Artifacts:**
- Wheel file (`.whl`)
- Source distribution (`.tar.gz`)
- Available for download from workflow runs

## Badge Status

Add these badges to your README.md to show CI status:

```markdown
[![CI](https://github.com/CampbellTrevor/Amorsize/workflows/CI/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions?query=workflow%3ACI)
```

## Local Testing

To run tests locally matching CI:

```bash
# Install dev dependencies
pip install -e ".[dev,full]"

# Run tests with coverage
pytest tests/ -v --tb=short --cov=amorsize --cov-report=xml --cov-report=term

# Build package
python -m build

# Check package
twine check dist/*
```

## Troubleshooting

### Test Failures
- Check the specific job logs in GitHub Actions
- Look for Python version-specific or OS-specific issues
- Use `fail-fast: false` to run all matrix combinations even if some fail

### Build Failures
- Verify pyproject.toml is correctly configured
- Check that all required files are included in MANIFEST.in
- Test build locally: `python -m build`

### Coverage Issues
- Codecov token may be required for private repositories
- Add `CODECOV_TOKEN` to repository secrets if needed
- Coverage upload failures are non-blocking (`fail_ci_if_error: false`)

## Maintenance

### Updating Actions
Check for updates to GitHub Actions periodically:
- `actions/checkout` (currently v4)
- `actions/setup-python` (currently v5)
- `codecov/codecov-action` (currently v4)
- `actions/upload-artifact` (currently v4)

### Adding New Python Versions
Update the `python-version` matrix in `ci.yml` when new Python versions are released.

### Modifying Test Matrix
To exclude specific combinations:
```yaml
matrix:
  exclude:
    - os: macos-latest
      python-version: '3.7'
```
