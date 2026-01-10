# GitHub Actions CI/CD Workflows

This directory contains automated workflows for continuous integration and deployment.

## Workflows

### 1. Test Suite (`test.yml`)

**Purpose:** Automated testing across multiple Python versions and operating systems.

**Triggers:**
- Push to `main` or `Iterate` branches
- Pull requests to `main` or `Iterate` branches
- Manual workflow dispatch

**Jobs:**

#### `test`
Tests the package across multiple configurations:
- **Python versions:** 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- **Operating systems:** Ubuntu (Linux), macOS, Windows
- **Total configurations:** 21 (7 Python versions × 3 OS)

Runs:
- Full test suite with pytest
- Code coverage on Ubuntu + Python 3.11 (uploaded to Codecov)

#### `test-minimal`
Tests package without optional dependencies (e.g., without `psutil`):
- **Python versions:** 3.7, 3.11, 3.13 (representative sample)
- **Operating system:** Ubuntu only

Ensures:
- Package works without optional dependencies
- Fallback strategies function correctly

#### `lint`
Code quality checks:
- **black**: Code formatting validation
- **isort**: Import sorting validation
- **flake8**: Linting for syntax errors and code style

*Note: Linting errors are informational only (continue-on-error: true) and won't fail the build.*

### 2. Build Package (`build.yml`)

**Purpose:** Validate package building and installation.

**Triggers:**
- Push to `main` or `Iterate` branches
- Pull requests to `main` or `Iterate` branches
- Manual workflow dispatch

**Jobs:**

#### `build`
Builds distribution packages:
- Source distribution (sdist)
- Wheel distribution (whl)
- Validates with `twine check`
- Uploads artifacts (retained for 7 days)

#### `install-test`
Tests installation from built packages:
- Installs wheel distribution
- Verifies imports work correctly
- Tests basic functionality

## Workflow Status

All workflows are configured to:
- Run on multiple Python versions (3.7-3.13)
- Test across operating systems where appropriate
- Provide detailed error reporting
- Upload artifacts and coverage reports

## Adding Badges to README

To add workflow status badges to your README, use:

```markdown
[![Test Suite](https://github.com/CampbellTrevor/Amorsize/actions/workflows/test.yml/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/test.yml)
[![Build Package](https://github.com/CampbellTrevor/Amorsize/actions/workflows/build.yml/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/build.yml)
```

## Configuration Details

### Python Version Support

The workflows test all versions declared in `pyproject.toml`:
- Python 3.7 (minimum supported)
- Python 3.8
- Python 3.9
- Python 3.10
- Python 3.11 (recommended for development)
- Python 3.12
- Python 3.13 (latest)

### Operating System Support

- **Linux (Ubuntu):** Primary platform, runs all jobs
- **macOS:** Full test coverage
- **Windows:** Full test coverage

This ensures cross-platform compatibility.

### Dependencies

Workflows automatically install:
- Production dependencies (from `pyproject.toml`)
- Optional dependencies: `psutil` (for `[full]` install)
- Development dependencies: `pytest`, `pytest-cov` (from `[dev]` install)
- Build tools: `build`, `twine`
- Linting tools: `black`, `isort`, `flake8` (lint job only)

## Local Testing

To replicate CI testing locally:

```bash
# Run full test suite
pytest tests/ -v --tb=short

# Run with coverage
pytest tests/ --cov=amorsize --cov-report=term-missing

# Check code formatting
black --check --diff amorsize/ tests/
isort --check-only --diff amorsize/ tests/

# Lint code
flake8 amorsize/ --select=E9,F63,F7,F82 --show-source
```

## Future Enhancements

Potential additions for future iterations:
- **Performance benchmarking:** Track performance over time
- **Documentation building:** Auto-generate and deploy docs
- **PyPI publishing:** Automated release to PyPI on tags
- **Security scanning:** Dependency vulnerability checks
- **Matrix testing:** Additional OS/architecture combinations

## Troubleshooting

### Workflow Failures

1. **Test failures:** Check the test logs in Actions tab
2. **Build failures:** Verify `pyproject.toml` configuration
3. **Import errors:** Ensure all dependencies are declared

### Skipped Tests

Some tests may be skipped on certain platforms or configurations. This is expected and handled by pytest markers.

## Maintenance

Workflows use pinned action versions for stability and security:
- `actions/checkout@v4`
- `actions/setup-python@v5`
- `actions/upload-artifact@v4.4.3` (latest stable)
- `actions/download-artifact@v4.1.3` (patched for CVE: arbitrary file write vulnerability)
- `codecov/codecov-action@v3`

**Security Note:** Version 4.1.3 of `actions/download-artifact` is used to address a critical arbitrary file write vulnerability (CVE) affecting versions 4.0.0 to 4.1.2. Always use the latest patched versions for artifact actions.

Update these periodically to get security fixes and new features.
