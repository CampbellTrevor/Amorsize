# GitHub Actions CI/CD Workflows

This directory contains automated workflows for continuous integration and continuous deployment.

## Workflows

### 1. Tests (`test.yml`)

Automated testing across multiple Python versions and operating systems.

**Triggers:**
- Push to `main` or `Iterate` branches
- Pull requests to `main` or `Iterate` branches

**Jobs:**
- **test**: Runs full test suite on Python 3.7-3.13 across Ubuntu, Windows, and macOS
- **test-minimal**: Tests without optional dependencies (psutil) to ensure core functionality works

**Test Matrix:**
- Operating Systems: Ubuntu, Windows, macOS
- Python Versions: 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- Note: Python 3.7 excluded on macOS (ARM64 compatibility)

### 2. Build (`build.yml`)

Package building and validation.

**Triggers:**
- Push to `main` or `Iterate` branches
- Pull requests to `main` or `Iterate` branches

**Steps:**
1. Build Python package (wheel and sdist)
2. Validate package with twine check
3. Test installation from built wheel
4. Upload build artifacts for review

**Artifacts:**
- Built packages stored for 90 days
- Available for download from workflow runs

### 3. Lint (`lint.yml`)

Code quality checks and linting.

**Triggers:**
- Push to `main` or `Iterate` branches
- Pull requests to `main` or `Iterate` branches

**Checks:**
- Python syntax errors (flake8 E9,F63,F7,F82)
- Code complexity and style (flake8, non-blocking)
- Import resolution verification

## Status Badges

Add these to your README.md to show workflow status:

```markdown
![Tests](https://github.com/CampbellTrevor/Amorsize/workflows/Tests/badge.svg)
![Build](https://github.com/CampbellTrevor/Amorsize/workflows/Build/badge.svg)
![Lint](https://github.com/CampbellTrevor/Amorsize/workflows/Lint/badge.svg)
```

## Local Testing

Before pushing, you can test locally:

```bash
# Run tests
pytest tests/ -v

# Build package
python -m build

# Check package
twine check dist/*

# Lint code
flake8 amorsize --count --select=E9,F63,F7,F82 --show-source --statistics
```

## Requirements

Workflows automatically install dependencies from `pyproject.toml`:
- **Full install**: `pip install -e ".[dev,full]"`
- **Minimal install**: `pip install -e .`

## Maintenance

### Adding New Python Versions

Update the `python-version` matrix in `test.yml`:

```yaml
matrix:
  python-version: ['3.7', '3.8', ..., '3.14']  # Add new version
```

### Modifying Test Parameters

Edit `pytest` command in workflow files:

```yaml
run: |
  pytest tests/ -v --tb=short --cov=amorsize  # Add coverage
```

### Troubleshooting

- **Workflow not running**: Check branch name matches triggers
- **Build failures**: Review GitHub Actions logs for specific errors
- **Matrix exclusions**: Some Python/OS combinations may not be supported

## Future Enhancements

Potential additions:
- Code coverage reporting (codecov/coveralls)
- PyPI publishing workflow
- Performance benchmarking
- Security scanning (bandit, safety)
- Documentation building and deployment
