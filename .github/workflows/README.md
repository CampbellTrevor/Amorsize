# GitHub Actions Workflows

This directory contains automated CI/CD workflows for the Amorsize project.

## Workflows

### 1. Tests (`test.yml`)

**Triggers:** Push and Pull Requests to `main` and `Iterate` branches

**Purpose:** Run comprehensive test suite across multiple Python versions and operating systems

**Test Matrix:**
- **Python versions:** 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- **Operating systems:** Ubuntu, macOS, Windows
- **Total combinations:** 20 (7 versions × 3 OS, excluding Python 3.7 on ubuntu-latest)

**Jobs:**
1. **test** - Run pytest test suite on all combinations
   - Install dependencies with `pip install -e ".[dev,full]"`
   - Run all tests with `pytest tests/ -v`
   - Verify package import works
   
2. **lint** - Code quality checks (Ubuntu + Python 3.11)
   - flake8: Check for syntax errors and code style
   - pylint: Static code analysis

**Note:** Linting errors are non-blocking (`continue-on-error: true`) to avoid breaking the build on style issues.

### 2. Build (`build.yml`)

**Triggers:** Push and Pull Requests to `main` and `Iterate` branches, plus releases

**Purpose:** Verify package builds correctly and can be installed

**Steps:**
1. Build wheel and source distribution with `python -m build`
2. Validate package with `twine check`
3. Test installation from wheel
4. Upload build artifacts (retained for 7 days)

**Outputs:**
- Wheel file: `amorsize-*.whl`
- Source distribution: `amorsize-*.tar.gz`
- Artifacts available for download from workflow run

### 3. Coverage (`coverage.yml`)

**Triggers:** Push and Pull Requests to `main` and `Iterate` branches

**Purpose:** Generate code coverage reports

**Steps:**
1. Run tests with coverage collection (`pytest-cov`)
2. Generate terminal and HTML coverage reports
3. Upload HTML coverage report as artifact (retained for 7 days)

**Outputs:**
- HTML coverage report available in artifacts
- Terminal coverage summary in workflow logs

## Workflow Status

Workflows will run automatically on:
- Every push to `main` or `Iterate` branches
- Every pull request to `main` or `Iterate` branches
- Every release creation (build workflow only)

## Local Validation

To run the same checks locally:

```bash
# Install dependencies
pip install -e ".[dev,full]"

# Run tests
pytest tests/ -v

# Run linting
pip install flake8 pylint
flake8 amorsize --count --select=E9,F63,F7,F82 --show-source --statistics
pylint amorsize --exit-zero --max-line-length=127

# Build package
pip install build twine
python -m build
twine check dist/*

# Run coverage
pip install pytest-cov
pytest tests/ --cov=amorsize --cov-report=term --cov-report=html
```

## Workflow Configuration

All workflows use:
- **actions/checkout@v4** - Latest checkout action
- **actions/setup-python@v5** - Latest Python setup with pip caching
- **actions/upload-artifact@v4** - Latest artifact upload

## Python Version Support

The project officially supports Python 3.7 through 3.13:
- Python 3.7-3.6: Tested on macOS and Windows (not available on ubuntu-latest)
- Python 3.8-3.13: Tested on all three platforms (Ubuntu, macOS, Windows)

## Continuous Integration Benefits

These workflows provide:
- ✅ **Cross-platform validation:** Catch OS-specific issues early
- ✅ **Multi-version testing:** Ensure compatibility across Python versions
- ✅ **Build verification:** Prevent packaging issues before release
- ✅ **Code quality:** Automated linting and style checks
- ✅ **Coverage tracking:** Monitor test coverage over time
- ✅ **Quick feedback:** Know immediately if changes break tests

## Future Enhancements

Potential additions:
- PyPI publishing workflow (when ready for release)
- Security scanning (bandit, safety)
- Documentation building and deployment
- Performance benchmarking
- Automated changelog generation
