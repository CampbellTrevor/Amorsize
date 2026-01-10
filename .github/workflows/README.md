# GitHub Actions Workflows

This directory contains the CI/CD automation workflows for Amorsize.

## Workflows

### CI Workflow (`ci.yml`)

**Triggers:**
- Push to `main` or `Iterate` branches
- Pull requests targeting `main` or `Iterate`

**Jobs:**

1. **Test** - Matrix testing across platforms and Python versions
   - Operating Systems: Ubuntu, Windows, macOS
   - Python Versions: 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
   - Runs full test suite with coverage reporting
   - Uploads coverage to Codecov (Ubuntu + Python 3.11 only)

2. **Lint** - Code quality checks (non-blocking)
   - black: Code formatting
   - isort: Import sorting
   - flake8: Linting and syntax checking
   - mypy: Type checking
   - All checks are warnings only (won't block CI)

3. **Build** - Package building
   - Builds wheel and source distributions
   - Validates package metadata with twine
   - Uploads artifacts for test-install job

4. **Test-Install** - Installation validation
   - Downloads built package
   - Tests wheel installation
   - Verifies imports and basic functionality

### Publish Workflow (`publish.yml`)

**Triggers:**
- Automatic: When a GitHub release is published (publishes to PyPI)
- Manual: Can be manually dispatched via GitHub Actions UI (publishes to Test PyPI only)

**Job:**
- Builds package
- Validates with twine
- Publishes to PyPI (releases only) or Test PyPI (manual dispatch only)
- **Safety**: Manual dispatch always uses Test PyPI to prevent accidental production releases

**Required Secrets:**
- `PYPI_API_TOKEN` - For publishing to PyPI
- `TEST_PYPI_API_TOKEN` - For publishing to Test PyPI

## Setup Instructions

### For Codecov (Optional)

1. Sign up at https://codecov.io with your GitHub account
2. Enable Amorsize repository
3. Get the upload token
4. Add as `CODECOV_TOKEN` repository secret (optional - public repos work without token)

### For PyPI Publishing (Required for releases)

1. Create an account on https://pypi.org
2. Generate an API token (Account Settings → API tokens)
3. Add as `PYPI_API_TOKEN` repository secret

For testing:
1. Create an account on https://test.pypi.org
2. Generate an API token
3. Add as `TEST_PYPI_API_TOKEN` repository secret

### Adding Repository Secrets

1. Go to repository Settings
2. Navigate to Secrets and variables → Actions
3. Click "New repository secret"
4. Add the secret name and value
5. Click "Add secret"

## Local Testing

To run similar checks locally:

```bash
# Install dependencies
pip install -e ".[full]"
pip install pytest pytest-cov black isort flake8 mypy

# Run tests with coverage
pytest tests/ -v --cov=amorsize --cov-report=term

# Check formatting
black --check amorsize/ tests/

# Check imports
isort --check-only amorsize/ tests/

# Lint
flake8 amorsize/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics

# Type check
mypy amorsize/ --ignore-missing-imports

# Build package
pip install build
python -m build

# Validate package
pip install twine
twine check dist/*
```

## Workflow Status

You can view the status of workflows:
- On the repository's "Actions" tab
- As badges in README.md (can be added)
- In pull request checks

## Notes

- All lint checks are non-blocking (continue-on-error: true) to avoid disrupting development
- Only critical issues (syntax errors, undefined names) will fail the build
- Coverage is only uploaded from Ubuntu + Python 3.11 to avoid duplicate reports
- Python 3.7 is excluded from macOS testing (not available on ARM64 runners)
