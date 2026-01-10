# GitHub Actions Workflows

This directory contains CI/CD workflows for Amorsize.

## Workflows

### 🧪 Test Suite (`test.yml`)
**Trigger:** Push/PR to main, develop, iterate branches

Runs comprehensive test suite across:
- **Operating Systems:** Ubuntu, Windows, macOS
- **Python Versions:** 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- **Total Combinations:** 20 matrix jobs (3 OS × 7 Python versions - 1 exclusion)

**Features:**
- Caches pip dependencies for faster runs
- Generates coverage report (Ubuntu + Python 3.11)
- Uploads coverage to Codecov
- Sets `AMORSIZE_TESTING=1` to prevent false positives in nested parallelism detection

**Note:** Python 3.7 excluded on macOS (not available on ARM64 runners)

### 🔍 Code Quality (`lint.yml`)
**Trigger:** Push/PR to main, develop, iterate branches

Performs basic code quality checks:
- Python syntax validation (py_compile)
- Import structure verification
- Package metadata validation

### 📦 Build Package (`build.yml`)
**Trigger:** Push/PR to main, develop, iterate branches

Builds and validates distribution packages:
- Builds wheel and source distribution
- Validates package with twine
- Tests wheel installation
- Uploads artifacts (retained for 7 days)

## Local Testing

### Run tests locally
```bash
# Install dependencies
pip install -e ".[dev,full]"

# Run test suite
AMORSIZE_TESTING=1 pytest tests/ -v

# Run with coverage
AMORSIZE_TESTING=1 pytest tests/ --cov=amorsize --cov-report=term
```

### Build package locally
```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Check package
twine check dist/*

# Test installation
pip install dist/*.whl
```

## Status Badges

Add these to your README.md to show CI status:

```markdown
[![Test Suite](https://github.com/CampbellTrevor/Amorsize/workflows/Test%20Suite/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/test.yml)
[![Code Quality](https://github.com/CampbellTrevor/Amorsize/workflows/Code%20Quality/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/lint.yml)
[![Build Package](https://github.com/CampbellTrevor/Amorsize/workflows/Build%20Package/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/build.yml)
```

## Workflow Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   GitHub Actions CI/CD                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Test Suite  │  │ Code Quality│  │ Build Pkg   │   │
│  │             │  │             │  │             │   │
│  │ 20 matrix   │  │ Python lint │  │ wheel + tar │   │
│  │ jobs        │  │ Import test │  │ twine check │   │
│  │ 3 OS x 7 Py │  │ Metadata    │  │ Upload dist │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Environment Variables

### `AMORSIZE_TESTING`
Set to `1` during test runs to prevent false positives in nested parallelism detection. This is important because:
- Test frameworks (pytest) load multiprocessing.pool
- This would trigger nested parallelism warnings
- Setting this variable disables detection during tests

## Maintenance

### Adding New Python Versions
1. Update matrix in `test.yml`: Add version to `python-version` array
2. Update classifiers in `pyproject.toml` if needed
3. Test locally with new version first

### Modifying Test Matrix
The matrix can be customized with:
- `exclude`: Skip specific OS/Python combinations
- `include`: Add special configurations
- `fail-fast`: Set to `true` to stop on first failure (currently `false`)

### Workflow Dependencies
All workflows use:
- `actions/checkout@v4` - Latest checkout action
- `actions/setup-python@v5` - Latest Python setup with pip caching
- `actions/upload-artifact@v4` - Latest artifact upload

## Troubleshooting

### Tests Failing on Specific OS
1. Check if OS-specific behavior is expected
2. Review test logs for OS-specific errors
3. Consider adding OS-specific skip markers

### Coverage Upload Fails
- Codecov token may be required for private repos
- Add `CODECOV_TOKEN` secret in repository settings
- Or set `fail_ci_if_error: false` to make it non-blocking (current setting)

### Build Package Fails
1. Check pyproject.toml syntax
2. Verify MANIFEST.in includes all needed files
3. Test locally with `python -m build`
