# GitHub Actions CI/CD Workflows

This directory contains automated workflows for continuous integration and deployment.

## Workflows

### 🧪 test.yml - Test Suite
**Triggers:** Push to main/Iterate/develop, Pull Requests, Manual dispatch

**Jobs:**
- **test**: Runs the full test suite across multiple Python versions (3.7-3.13) and operating systems (Ubuntu, macOS, Windows)
  - Executes all tests with strict marker validation
  - Generates coverage report for Ubuntu Python 3.12
  - Uploads coverage to Codecov (if token configured)
  
- **test-minimal**: Tests installation without optional dependencies
  - Ensures core functionality works without psutil
  - Validates package can run in minimal environments

**Matrix Strategy:**
- Python: 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- OS: Ubuntu, macOS, Windows
- Note: Python 3.7 excluded from modern runners (not available)

### 📦 build.yml - Build & Package
**Triggers:** Push to main/Iterate/develop, Tags (v*), Pull Requests, Manual dispatch

**Jobs:**
- **build**: Creates distribution packages
  - Builds source distribution (sdist) and wheel
  - Validates packages with twine
  - Uploads artifacts for 7 days retention
  
- **install-test**: Validates installation
  - Downloads built artifacts
  - Installs from wheel
  - Tests import and basic functionality
  - Ensures optimizer works correctly

**Outputs:**
- `amorsize-0.1.0-py3-none-any.whl`
- `amorsize-0.1.0.tar.gz`

### 🔍 lint.yml - Code Quality
**Triggers:** Push to main/Iterate/develop, Pull Requests, Manual dispatch

**Jobs:**
- **lint**: Runs multiple code quality checks
  - **flake8**: Syntax errors, undefined names, complexity
  - **isort**: Import sorting validation
  - **bandit**: Security vulnerability scanning
  
- **format-check**: Code formatting validation
  - **black**: Code style consistency
  
**Note:** All checks are non-blocking (continue-on-error: true) to provide feedback without failing builds

## Status Badges

Add these to your README.md:

```markdown
![Test Suite](https://github.com/CampbellTrevor/Amorsize/workflows/Test%20Suite/badge.svg)
![Build & Package](https://github.com/CampbellTrevor/Amorsize/workflows/Build%20%26%20Package/badge.svg)
![Code Quality](https://github.com/CampbellTrevor/Amorsize/workflows/Code%20Quality/badge.svg)
```

## Configuration

### Codecov (Optional)
To enable coverage reporting:
1. Sign up at https://codecov.io
2. Add repository
3. Add `CODECOV_TOKEN` to GitHub repository secrets

### Manual Workflow Dispatch
All workflows support manual triggering via GitHub Actions UI:
1. Go to Actions tab
2. Select workflow
3. Click "Run workflow"

## Local Testing

Before pushing, you can validate workflows locally:

```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"

# Run tests locally
pytest tests/ -v --tb=short --strict-markers

# Build package locally
python -m build

# Check package
twine check dist/*
```

## Workflow Details

### Python Version Support
- **Full Support**: 3.8-3.13 (tested on all platforms)
- **Limited**: 3.7 (excluded from modern runners)

### Operating Systems
- **Ubuntu**: Primary platform, generates coverage
- **macOS**: Darwin platform testing
- **Windows**: Windows platform testing

### Caching
All workflows use pip caching to speed up dependency installation:
- Cache key based on OS and requirements
- Automatically invalidated when dependencies change

## Maintenance

### Adding New Dependencies
1. Update `pyproject.toml`
2. Workflows automatically pick up changes
3. No workflow modifications needed

### Adding New Tests
1. Add test files to `tests/` directory
2. Follow naming convention: `test_*.py`
3. Workflows automatically discover and run new tests

### Updating Python Versions
Edit matrix in `test.yml`:
```yaml
matrix:
  python-version: ['3.8', '3.9', '3.10', '3.11', '3.12', '3.13', '3.14']
```

## Troubleshooting

### Test Failures
- Check workflow logs in GitHub Actions tab
- Run tests locally with same Python version
- Ensure all dependencies in `pyproject.toml`

### Build Failures
- Verify `pyproject.toml` syntax
- Test build locally: `python -m build`
- Check twine output for package issues

### Coverage Upload Failures
- Verify `CODECOV_TOKEN` is set
- Check Codecov service status
- Coverage upload is non-blocking (won't fail CI)

## Best Practices

1. **Green CI**: Keep all workflows passing
2. **Fast Feedback**: Workflows optimized for speed
3. **Non-Blocking Lints**: Code quality checks provide feedback without blocking
4. **Matrix Testing**: Comprehensive platform coverage
5. **Artifact Retention**: Build artifacts kept for 7 days
