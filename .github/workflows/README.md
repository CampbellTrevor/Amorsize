# GitHub Actions Workflows

This directory contains CI/CD workflows for the Amorsize project.

## Workflows

### 1. Tests (`test.yml`)

**Trigger:** Push/PR to main, Iterate, develop branches

**Purpose:** Run comprehensive test suite across multiple Python versions and operating systems

**Matrix Testing:**
- Python versions: 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- Operating systems: Ubuntu, Windows, macOS
- Total combinations: ~20 test jobs

**Features:**
- Full test suite with pytest
- Code coverage reporting (uploaded to Codecov)
- Test with and without optional dependencies (psutil)
- Validates cross-platform compatibility

**Badge:**
```markdown
![Tests](https://github.com/CampbellTrevor/Amorsize/workflows/Tests/badge.svg)
```

### 2. Build & Package (`build.yml`)

**Trigger:** Push/PR to main, Iterate branches; Version tags

**Purpose:** Build distribution packages and verify installation

**Features:**
- Builds both wheel and source distribution
- Validates package with twine
- Tests installation from both wheel and sdist
- Verifies import functionality
- Runs basic functionality tests
- Uploads build artifacts

**Badge:**
```markdown
![Build](https://github.com/CampbellTrevor/Amorsize/workflows/Build%20%26%20Package/badge.svg)
```

### 3. Code Quality (`lint.yml`)

**Trigger:** Push/PR to main, Iterate, develop branches

**Purpose:** Enforce code quality standards and security

**Linting Tools:**
- **flake8**: Python syntax and style checking
- **black**: Code formatting verification
- **isort**: Import statement ordering
- **pylint**: Comprehensive linting
- **mypy**: Static type checking
- **bandit**: Security vulnerability scanning
- **safety**: Dependency security checking

**Note:** Most checks use `continue-on-error: true` to avoid blocking PRs while establishing baselines

**Badge:**
```markdown
![Code Quality](https://github.com/CampbellTrevor/Amorsize/workflows/Code%20Quality/badge.svg)
```

## Adding Workflow Status Badges

Add these badges to the README.md to show workflow status:

```markdown
[![Tests](https://github.com/CampbellTrevor/Amorsize/workflows/Tests/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/test.yml)
[![Build](https://github.com/CampbellTrevor/Amorsize/workflows/Build%20%26%20Package/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/build.yml)
[![Code Quality](https://github.com/CampbellTrevor/Amorsize/workflows/Code%20Quality/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/lint.yml)
```

## Workflow Configuration

### Python Version Support
The test workflow validates Python 3.7-3.13 compatibility as declared in `pyproject.toml`.

### Operating System Support
Tests run on:
- **Ubuntu** (Linux): Primary development platform
- **Windows**: For Windows-specific multiprocessing behavior (spawn mode)
- **macOS**: For macOS-specific multiprocessing behavior

### Coverage Reporting
Test coverage is collected on Ubuntu with Python 3.12 and uploaded to Codecov (requires `CODECOV_TOKEN` secret).

### Build Artifacts
Build artifacts (wheel and sdist) are retained for 30 days and can be downloaded from workflow runs.

## Future Enhancements

### Potential Additions:
1. **Performance benchmarking workflow** - Track performance over time
2. **Documentation deployment** - Auto-deploy docs on updates
3. **PyPI publishing workflow** - Automated release to PyPI on version tags
4. **Dependency updates** - Automated dependency updates with Dependabot
5. **Container testing** - Test in Docker containers to validate cgroup detection

### PyPI Publishing (Template)
When ready to publish to PyPI, add a workflow like:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  pypi-publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: |
          pip install build twine
          python -m build
          twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
```

## Troubleshooting

### Test Failures
- Check workflow logs in the Actions tab
- Failures on specific OS/Python combinations may indicate compatibility issues
- Multiprocessing behavior differs between fork (Linux) and spawn (Windows/macOS)

### Build Failures
- Ensure `pyproject.toml` is valid
- Check that all required files are included in MANIFEST.in
- Verify setuptools compatibility

### Linting Failures
- Most linting jobs use `continue-on-error: true` initially
- Review reports and gradually enforce stricter rules
- Use `black` for automatic formatting: `black amorsize/ tests/`

## Local Testing

Test workflows locally before pushing:

```bash
# Run tests
pytest tests/ -v --cov=amorsize

# Check code formatting
black --check amorsize/ tests/
isort --check-only amorsize/ tests/

# Run linters
flake8 amorsize/
pylint amorsize/

# Build package
python -m build
twine check dist/*

# Test installation
pip install dist/*.whl
python -c "from amorsize import optimize"
```

## Secrets Configuration

### Required Secrets (optional):
- `CODECOV_TOKEN`: For uploading coverage reports to Codecov
- `PYPI_TOKEN`: For automated PyPI publishing (when ready)

Configure secrets in: Repository Settings → Secrets and variables → Actions

## Monitoring

Monitor workflow runs:
- **Actions Tab**: https://github.com/CampbellTrevor/Amorsize/actions
- **Test Results**: Check individual job logs for failures
- **Coverage**: Review coverage reports in Codecov (if configured)
- **Build Artifacts**: Download from successful workflow runs
