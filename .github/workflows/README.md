# GitHub Actions Workflows

This directory contains CI/CD automation workflows for the Amorsize project.

## Workflows

### test.yml - Test Suite
**Trigger:** Push and PR to `main` or `Iterate` branches
**Purpose:** Run comprehensive test suite across all supported Python versions

**Jobs:**
- `test`: Runs tests on Python 3.7-3.13 with full dependencies
- `test-minimal`: Tests without optional dependencies (psutil)
- `coverage`: Generates code coverage reports and uploads to Codecov

**Key Features:**
- Matrix testing across Python 3.7 through 3.13
- Tests both with and without optional dependencies
- Code coverage tracking
- Fast fail disabled to see all Python version results

### build.yml - Build & Package
**Trigger:** Push and PR to `main` or `Iterate` branches, tags starting with 'v'
**Purpose:** Build distribution packages and verify installation

**Jobs:**
- `build`: Builds wheel and source distribution using PEP 517
- `install-test`: Verifies package installs and imports correctly
- `multi-platform`: Tests on Ubuntu, macOS, and Windows

**Key Features:**
- PEP 517 compliant build process
- Package validation with twine
- Cross-platform compatibility testing
- Installation verification from built wheel

### lint.yml - Code Quality
**Trigger:** Push and PR to `main` or `Iterate` branches
**Purpose:** Automated code quality and security checks

**Jobs:**
- `lint`: Runs multiple linters (flake8, black, isort, mypy, pylint)
- `security`: Security scanning with bandit and dependency checking

**Key Features:**
- Multiple code quality tools
- Non-blocking (continue-on-error) for informational purposes
- Security vulnerability detection
- Artifact upload for detailed reports

### publish.yml - Publish to PyPI
**Trigger:** GitHub release or manual workflow dispatch
**Purpose:** Publish package to PyPI

**Jobs:**
- `publish`: Builds and publishes to PyPI or Test PyPI

**Key Features:**
- Automatic publishing on GitHub release
- Manual publishing option with workflow_dispatch
- Test PyPI support for verification
- Release artifact upload

## Configuration Requirements

### Secrets
The following secrets need to be configured in GitHub repository settings:

- `PYPI_API_TOKEN`: API token for publishing to PyPI (for releases)
- `TEST_PYPI_API_TOKEN`: API token for Test PyPI (optional, for testing)

### Codecov (Optional)
To enable code coverage reporting:
1. Sign up at https://codecov.io
2. Add your repository
3. Coverage reports will be uploaded automatically

## Usage

### Running Tests Locally
```bash
# Install test dependencies
pip install -e ".[full,dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=amorsize --cov-report=term-missing
```

### Building Locally
```bash
# Install build dependencies
pip install build twine

# Build package
python -m build

# Check package
twine check dist/*
```

### Manual Workflow Dispatch
To manually trigger workflows:
1. Go to Actions tab in GitHub
2. Select the workflow
3. Click "Run workflow"
4. Choose branch and fill in any inputs

## Status Badges

Add these to your README.md to show workflow status:

```markdown
[![Test Suite](https://github.com/CampbellTrevor/Amorsize/actions/workflows/test.yml/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/test.yml)
[![Build & Package](https://github.com/CampbellTrevor/Amorsize/actions/workflows/build.yml/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/build.yml)
[![Code Quality](https://github.com/CampbellTrevor/Amorsize/actions/workflows/lint.yml/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/lint.yml)
```

## Continuous Integration Strategy

The workflows implement a comprehensive CI strategy:

1. **Every PR/Push:**
   - Full test suite across all Python versions
   - Build verification
   - Code quality checks
   - Security scanning

2. **On Release:**
   - All above checks
   - Automatic PyPI publishing
   - Release artifact upload

3. **Multi-Platform:**
   - Linux, macOS, Windows testing
   - Ensures cross-platform compatibility

## Maintenance

### Updating Python Versions
When adding/removing Python version support:
1. Update `python-version` matrix in `test.yml`
2. Update classifiers in `pyproject.toml`
3. Update README.md documentation

### Updating Dependencies
GitHub Actions automatically uses latest patch versions of actions (e.g., `@v4`).
Manual updates required for:
- Python version specifications
- pip package versions in workflows

**Security Note:** We explicitly pin `actions/download-artifact@v4.1.3` (not `@v4`) 
due to a security vulnerability (arbitrary file write via artifact extraction) in 
versions >= 4.0.0, < 4.1.3. This ensures the patched version is always used.

## Troubleshooting

### Test Failures
- Check workflow logs in Actions tab
- Run tests locally to reproduce
- Ensure all dependencies are installed

### Build Failures
- Verify pyproject.toml configuration
- Check for missing files in MANIFEST.in
- Test build locally with `python -m build`

### Publication Failures
- Verify API tokens are configured correctly
- Check package version isn't already published
- Test with Test PyPI first
