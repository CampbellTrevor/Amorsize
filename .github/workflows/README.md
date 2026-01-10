# GitHub Actions Workflows

This directory contains CI/CD automation workflows for the Amorsize project.

## Workflows

### 1. Tests (`test.yml`)

**Triggers:** Push or PR to `main`, `Iterate`, or `develop` branches

**Purpose:** Runs the complete test suite across multiple Python versions and operating systems.

**Matrix:**
- **Operating Systems:** Ubuntu, Windows, macOS
- **Python Versions:** 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- **Total Combinations:** 20 (macOS excludes Python 3.7 due to ARM compatibility)

**Steps:**
1. Checkout code
2. Set up Python with pip caching
3. Install dependencies with `[full,dev]` extras
4. Run pytest with verbose output
5. Test basic imports

**Benefits:**
- Ensures compatibility across all supported Python versions
- Validates cross-platform behavior
- Catches regressions early

### 2. Build (`build.yml`)

**Triggers:** 
- Push or PR to `main`, `Iterate`, or `develop` branches
- Release publication

**Purpose:** Validates that the package builds correctly and can be installed.

**Steps:**
1. Checkout code
2. Set up Python 3.11
3. Install build tools (`build`, `twine`)
4. Build source distribution and wheel
5. Check package metadata with `twine check`
6. Test wheel installation and import
7. Upload artifacts for 30 days

**Benefits:**
- Ensures package can be built successfully
- Validates metadata and package structure
- Prepares artifacts for PyPI publication
- Verifies wheel installation works

### 3. Code Quality (`quality.yml`)

**Triggers:** Push or PR to `main`, `Iterate`, or `develop` branches

**Purpose:** Performs basic code quality checks.

**Steps:**
1. Checkout code
2. Set up Python 3.11
3. Install dependencies
4. Check package metadata and exports
5. Verify `pyproject.toml` is valid TOML
6. Compile all Python files to check for syntax errors
7. Validate all example files

**Benefits:**
- Catches syntax errors early
- Validates package exports
- Ensures examples remain valid
- Verifies configuration files

## Status Badges

Add these to your README.md to show workflow status:

```markdown
![Tests](https://github.com/CampbellTrevor/Amorsize/actions/workflows/test.yml/badge.svg)
![Build](https://github.com/CampbellTrevor/Amorsize/actions/workflows/build.yml/badge.svg)
![Code Quality](https://github.com/CampbellTrevor/Amorsize/actions/workflows/quality.yml/badge.svg)
```

## Local Testing

Before pushing, you can run tests locally:

```bash
# Run tests
pytest tests/ -v

# Build package
python -m build

# Check package
twine check dist/*
```

## Adding New Workflows

When adding new workflows:
1. Follow GitHub Actions YAML syntax
2. Use `actions/checkout@v4` for checkout
3. Use `actions/setup-python@v5` for Python setup
4. Enable pip caching with `cache: 'pip'`
5. Use descriptive names and comments
6. Test locally before committing

## Maintenance

- **Python versions:** Update when adding/removing Python support
- **Actions versions:** Keep action versions up to date (currently v4/v5)
- **Dependencies:** Keep in sync with `pyproject.toml` requirements
- **OS compatibility:** Adjust matrix as needed for platform support
