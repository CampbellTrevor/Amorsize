# GitHub Actions Workflows

This directory contains CI/CD automation workflows for the Amorsize project.

## Workflows

### 🧪 Test Suite (`test.yml`)

Comprehensive automated testing across platforms and Python versions.

**Matrix:** 21 combinations
- **Operating Systems:** Ubuntu, Windows, macOS
- **Python Versions:** 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13

**Features:**
- Full test suite execution with pytest
- Coverage reporting (Ubuntu + Python 3.11)
- Codecov integration
- Minimal dependency testing (without psutil)

**Triggers:**
- Push to main, Iterate, develop
- Pull requests to main, Iterate, develop
- Manual workflow dispatch

### 📋 Code Quality (`lint.yml`)

Automated code quality and syntax checks.

**Checks:**
- Critical syntax errors (E9, F63, F7, F82) - fails build
- Code complexity and line length
- Pylint analysis
- Import verification

**Triggers:**
- Push to main, Iterate, develop
- Pull requests to main, Iterate, develop
- Manual workflow dispatch

### 📦 Build & Package (`build.yml`)

Package building and installation verification.

**Jobs:**
1. **Build:** Create wheel and validate with twine
2. **Verify:** Test installation methods (wheel + editable)

**Features:**
- pyproject.toml validation
- Wheel and source distribution building
- PyPI compatibility checks with twine
- Installation verification
- Artifact uploading (7-day retention)

**Triggers:**
- Push to main, Iterate, develop
- Pull requests to main, Iterate, develop
- Release creation
- Manual workflow dispatch

## Status Badges

Add to README.md:

```markdown
[![Tests](https://github.com/CampbellTrevor/Amorsize/workflows/Test%20Suite/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/test.yml)
[![Code Quality](https://github.com/CampbellTrevor/Amorsize/workflows/Code%20Quality/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/lint.yml)
[![Build](https://github.com/CampbellTrevor/Amorsize/workflows/Build%20%26%20Package/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/build.yml)
```

## Local Testing

Replicate workflow steps locally:

### Test Suite
```bash
# Install dependencies
pip install -e ".[dev,full]"

# Run tests
pytest tests/ -v --tb=short --strict-markers

# With coverage
pytest tests/ --cov=amorsize --cov-report=xml --cov-report=term-missing
```

### Code Quality
```bash
# Install linters
pip install flake8 pylint

# Critical syntax check
flake8 amorsize --count --select=E9,F63,F7,F82 --show-source --statistics

# Full check
flake8 amorsize --count --max-complexity=10 --max-line-length=127 --statistics

# Pylint
pylint amorsize --max-line-length=127
```

### Build & Package
```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Check distribution
twine check dist/*

# Test installation
pip install dist/*.whl
python -c "from amorsize import optimize; print('✓ Works')"
```

## Notes

- Python 3.13 is excluded from Windows/macOS runners (may not be available yet)
- Coverage reporting runs only on Ubuntu + Python 3.11 for efficiency
- All workflows support manual triggering via GitHub UI
- Artifacts are kept for 7 days for inspection
