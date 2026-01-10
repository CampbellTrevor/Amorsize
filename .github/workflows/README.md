# GitHub Actions CI/CD Workflows

This directory contains GitHub Actions workflows for continuous integration and deployment.

## Workflows

### 1. Test Suite (`test.yml`)

**Purpose:** Runs the full test suite across multiple Python versions and operating systems.

**Triggers:**
- Push to `main`, `Iterate`, or `develop` branches
- Pull requests targeting these branches

**Matrix:**
- **OS:** Ubuntu, Windows, macOS
- **Python:** 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- **Total combinations:** 20 (excludes Python 3.7 on macOS ARM64)

**What it does:**
1. Checks out the code
2. Sets up Python for the matrix version
3. Installs package and test dependencies
4. Installs optional dependencies (psutil)
5. Runs pytest with coverage
6. Uploads coverage to Codecov (Ubuntu + Python 3.12 only)

**Benefits:**
- Ensures compatibility across Python versions
- Validates cross-platform functionality
- Catches regressions early
- Provides coverage metrics

### 2. Build Package (`build.yml`)

**Purpose:** Verifies that the package builds correctly and can be installed.

**Triggers:**
- Push to `main`, `Iterate`, or `develop` branches
- Pull requests targeting these branches

**What it does:**
1. Checks out the code
2. Sets up Python 3.12
3. Installs build tools (build, twine)
4. Builds wheel and source distribution
5. Verifies package metadata with twine
6. Tests wheel installation
7. Uploads build artifacts

**Benefits:**
- Validates pyproject.toml configuration
- Ensures package is installable
- Catches distribution issues early
- Prepares artifacts for potential PyPI publication

### 3. Code Quality (`lint.yml`)

**Purpose:** Performs basic code quality checks.

**Triggers:**
- Push to `main`, `Iterate`, or `develop` branches
- Pull requests targeting these branches

**What it does:**
1. Checks out the code
2. Sets up Python 3.12
3. Verifies all package imports work
4. Checks for syntax errors
5. Validates pyproject.toml format

**Benefits:**
- Catches import errors
- Validates Python syntax
- Ensures packaging configuration is correct
- Quick feedback on basic issues

## Workflow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Push/PR                          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ├──────────────┬──────────────┬──────────────┐
                 ▼              ▼              ▼              │
         ┌───────────┐  ┌──────────┐  ┌──────────────┐       │
         │   Test    │  │  Build   │  │ Code Quality │       │
         │   Suite   │  │ Package  │  │    Checks    │       │
         └───────────┘  └──────────┘  └──────────────┘       │
                 │              │              │              │
                 │              │              │              │
                 ▼              ▼              ▼              │
         ┌───────────┐  ┌──────────┐  ┌──────────────┐       │
         │ 20 matrix │  │  Verify  │  │   Validate   │       │
         │   jobs    │  │ artifacts│  │    syntax    │       │
         └───────────┘  └──────────┘  └──────────────┘       │
                 │              │              │              │
                 └──────────────┴──────────────┴──────────────┘
                                 │
                                 ▼
                         ┌──────────────┐
                         │  All checks  │
                         │    passed    │
                         └──────────────┘
```

## CI/CD Best Practices Implemented

### ✅ Fast Feedback
- Jobs run in parallel
- Quick quality checks complete first
- Matrix strategy for comprehensive testing

### ✅ Fail-Fast Disabled
- `fail-fast: false` in test matrix
- Allows all Python versions to be tested even if one fails
- Better visibility into compatibility issues

### ✅ Comprehensive Coverage
- Multiple Python versions (3.7-3.13)
- Multiple operating systems (Linux, Windows, macOS)
- Full test suite execution

### ✅ Artifact Preservation
- Build artifacts uploaded for inspection
- Can be used for manual testing or deployment

### ✅ Optional Dependencies
- psutil installation continues on error
- Ensures core functionality is tested even without optional deps

### ✅ Modern Actions
- Uses latest action versions (@v4, @v5)
- Compatible with current GitHub Actions features

## Adding New Workflows

To add a new workflow:

1. Create a new YAML file in `.github/workflows/`
2. Define the trigger events (`on:`)
3. Define jobs with appropriate steps
4. Test locally if possible (act, nektos/act)
5. Commit and push to trigger the workflow

## Local Testing

While GitHub Actions runs in the cloud, you can test locally:

```bash
# Install dependencies
pip install -e .
pip install pytest pytest-cov

# Run tests locally (mimics CI)
pytest tests/ -v --tb=short --cov=amorsize

# Build package locally
pip install build twine
python -m build
twine check dist/*

# Verify imports
python -c "from amorsize import optimize, execute"
```

## Status Badges

Add these to your README.md to show CI status:

```markdown
![Test Suite](https://github.com/CampbellTrevor/Amorsize/actions/workflows/test.yml/badge.svg)
![Build](https://github.com/CampbellTrevor/Amorsize/actions/workflows/build.yml/badge.svg)
![Code Quality](https://github.com/CampbellTrevor/Amorsize/actions/workflows/lint.yml/badge.svg)
```

## Troubleshooting

### Tests fail on specific Python version
- Check if dependencies are available for that version
- Review compatibility in pyproject.toml
- Consider excluding that version from matrix

### Build fails
- Verify pyproject.toml syntax
- Check that all required files are included
- Ensure MANIFEST.in is correct (for sdist)

### Import errors
- Check __init__.py exports
- Verify package structure
- Ensure all dependencies are installed

## Future Enhancements

Possible additions:
- **Linting:** Add flake8, black, or ruff for code style
- **Type Checking:** Add mypy for static type analysis
- **Security:** Add bandit for security checks
- **Documentation:** Add workflow to build and publish docs
- **Release:** Add workflow for automated PyPI publishing
- **Performance:** Add benchmarking workflow to track performance

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Python setup-python action](https://github.com/actions/setup-python)
- [Upload artifacts action](https://github.com/actions/upload-artifact)
- [Codecov action](https://github.com/codecov/codecov-action)
