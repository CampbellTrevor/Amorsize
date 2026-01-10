# GitHub Actions Workflows

This directory contains CI/CD workflows for automated testing, code quality checks, and package building.

## Workflows

### 1. Test Suite (`test.yml`)

**Triggers:** Push to main/Iterate, Pull Requests, Manual dispatch

**Purpose:** Runs comprehensive test suite across multiple Python versions and operating systems

**Jobs:**
- **test**: Runs pytest on Python 3.7-3.13 across Ubuntu, macOS, and Windows
  - Generates coverage reports
  - Uploads coverage to Codecov (for Python 3.11 on Ubuntu)
- **test-minimal**: Tests without optional dependencies (psutil)
  - Ensures core functionality works without extras

**Usage:**
- Automatically runs on every push and PR
- Helps ensure compatibility across Python versions and OS
- Provides coverage metrics for code quality

### 2. Code Quality (`lint.yml`)

**Triggers:** Push to main/Iterate, Pull Requests, Manual dispatch

**Purpose:** Enforces code quality standards through linting and type checking

**Jobs:**
- **lint**: Runs flake8 for Python syntax and style checks
  - Fails on syntax errors or undefined names
  - Warns on complexity and style issues
- **type-check**: Runs mypy for static type checking (informational)
  - Does not fail CI (informational only)
  - Helps catch type-related issues

**Usage:**
- Automatically runs on every push and PR
- Ensures code follows Python best practices
- Catches common errors before they reach production

### 3. Build Package (`build.yml`)

**Triggers:** Push to main/Iterate, Pull Requests, Tags (v*), Manual dispatch

**Purpose:** Builds distribution packages and verifies installation

**Jobs:**
- **build**: Creates wheel and sdist packages
  - Validates packages with twine
  - Tests wheel installation
  - Uploads build artifacts
- **verify-install**: Tests package installation on multiple OS
  - Downloads and installs built wheel
  - Verifies imports and basic functionality
  - Ensures package works cross-platform

**Usage:**
- Automatically runs on every push and PR
- Ensures package builds correctly
- Prepares artifacts for release

### 4. Publish to PyPI (`publish.yml`)

**Triggers:** Release published, Manual dispatch

**Purpose:** Publishes package to PyPI or TestPyPI

**Requirements:**
- GitHub secrets must be configured:
  - `PYPI_API_TOKEN`: Token for PyPI (production)
  - `TEST_PYPI_API_TOKEN`: Token for TestPyPI (testing)

**Jobs:**
- **publish**: Builds and uploads package to PyPI
  - Can publish to TestPyPI for testing (manual dispatch)
  - Publishes to PyPI on release creation
  - Attaches packages as release assets

**Usage:**
- For TestPyPI: Run workflow manually with `test-pypi: true`
- For PyPI: Create a GitHub release with a tag (e.g., v0.1.0)
- Requires API tokens to be configured in repository secrets

## Status Badges

Add these badges to your README.md to show workflow status:

```markdown
![Test Suite](https://github.com/CampbellTrevor/Amorsize/actions/workflows/test.yml/badge.svg)
![Code Quality](https://github.com/CampbellTrevor/Amorsize/actions/workflows/lint.yml/badge.svg)
![Build Package](https://github.com/CampbellTrevor/Amorsize/actions/workflows/build.yml/badge.svg)
```

## Manual Workflow Dispatch

All workflows can be triggered manually:

1. Go to the "Actions" tab in GitHub
2. Select the workflow you want to run
3. Click "Run workflow"
4. Choose the branch and any inputs (if applicable)

## Development Tips

### Running Tests Locally

Before pushing, run tests locally to catch issues:

```bash
# Install dependencies
pip install -e .
pip install pytest pytest-cov psutil

# Run full test suite
pytest -v --cov=amorsize

# Run specific test file
pytest tests/test_optimizer.py -v

# Run without psutil
pytest -v -k "not psutil"
```

### Linting Locally

Check code quality before pushing:

```bash
# Install linting tools
pip install flake8

# Run flake8
flake8 amorsize --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 amorsize --count --exit-zero --max-complexity=15 --max-line-length=127
```

### Building Package Locally

Test package building:

```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Check package
twine check dist/*

# Test installation
pip install dist/*.whl
python -c "from amorsize import optimize; print('✓ Works')"
```

## Troubleshooting

### Tests Failing on Specific Python Version

- Check if the issue is version-specific
- Review Python version compatibility in pyproject.toml
- Some features may not be available in older Python versions

### Build Artifacts Not Uploaded

- Ensure the build job completed successfully
- Check artifact retention period (default: 7 days)
- Artifacts are automatically cleaned up after retention period

### PyPI Publishing Failed

- Verify API tokens are correctly configured
- Check if version number already exists on PyPI
- Ensure package passes twine checks
- Review PyPI upload logs for specific errors

## Maintenance

### Updating Python Versions

When new Python versions are released, update the version matrix:

```yaml
matrix:
  python-version: ['3.7', '3.8', '3.9', '3.10', '3.11', '3.12', '3.13', '3.14']
```

### Updating GitHub Actions

Keep actions up to date:

- `actions/checkout` (currently v4)
- `actions/setup-python` (currently v5)
- `actions/upload-artifact` (currently v4)
- `actions/download-artifact` (currently v4)
- `codecov/codecov-action` (currently v4)

### Adding New Workflows

To add new workflows:

1. Create new `.yml` file in `.github/workflows/`
2. Define trigger events (`on:`)
3. Add jobs and steps
4. Test with manual dispatch first
5. Update this README with workflow documentation

## Best Practices

1. **Fail Fast**: Use `fail-fast: false` to see all test results
2. **Cache Dependencies**: Consider adding pip caching for faster builds
3. **Matrix Testing**: Test on multiple Python versions and OS
4. **Artifact Retention**: Set appropriate retention periods
5. **Secret Management**: Never commit secrets; use GitHub secrets
6. **Workflow Permissions**: Use minimal required permissions
7. **Manual Testing**: Always test workflows manually before relying on them

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Python Package Publishing](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [PyPI Publishing Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
