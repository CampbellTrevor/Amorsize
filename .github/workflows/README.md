# GitHub Actions Workflows

This directory contains CI/CD workflows for the Amorsize project.

## Workflows

### test.yml - Continuous Testing
**Trigger:** Push to `main` or `Iterate` branches, and pull requests
**Purpose:** Run comprehensive test suite across multiple Python versions and operating systems

**Test Matrix:**
- **Python versions:** 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- **Operating systems:** Ubuntu (Linux), Windows, macOS
- **Total combinations:** 21 test configurations

**What it does:**
1. Checks out the code
2. Sets up Python environment
3. Installs dependencies (pytest, pytest-cov, and package with full extras)
4. Runs test suite with coverage reporting
5. Uploads coverage report artifact (Ubuntu + Python 3.11 only)

**Viewing results:**
- Check the "Actions" tab in GitHub
- Green checkmark = all tests passed across all platforms
- Red X = at least one test failed

---

### build.yml - Package Building
**Trigger:** Push to `main` or `Iterate` branches, pull requests, and releases
**Purpose:** Build distribution packages and verify integrity

**What it does:**
1. Builds both wheel (.whl) and source (.tar.gz) distributions
2. Verifies package metadata with `twine check`
3. Tests installation from built wheel
4. Uploads build artifacts for 30 days

**Artifacts:**
- Wheel distribution: `amorsize-<version>-py3-none-any.whl`
- Source distribution: `amorsize-<version>.tar.gz`

---

### publish.yml - PyPI Publication
**Trigger:** Manual dispatch or GitHub release
**Purpose:** Publish package to PyPI or Test PyPI

**Requirements:**
- Repository secrets must be configured:
  - `PYPI_API_TOKEN` - For production PyPI
  - `TEST_PYPI_API_TOKEN` - For Test PyPI

**Usage:**

**Option 1: Automatic (on release)**
1. Create a new release on GitHub
2. Workflow automatically publishes to PyPI

**Option 2: Manual dispatch**
1. Go to "Actions" tab → "Publish to PyPI"
2. Click "Run workflow"
3. Select environment (testpypi or pypi)
4. Workflow builds and publishes

**Testing before production:**
```bash
# Always test on Test PyPI first
1. Run workflow manually with "testpypi" selected
2. Verify package: pip install -i https://test.pypi.org/simple/ amorsize
3. Test functionality
4. If all good, publish to production PyPI
```

---

## Setting Up Secrets

To enable PyPI publishing, configure these secrets in repository settings:

1. Go to repository → Settings → Secrets and variables → Actions
2. Add secrets:
   - `PYPI_API_TOKEN`: Get from https://pypi.org/manage/account/token/
   - `TEST_PYPI_API_TOKEN`: Get from https://test.pypi.org/manage/account/token/

---

## Status Badges

Add these badges to README.md to show CI status:

```markdown
[![Tests](https://github.com/CampbellTrevor/Amorsize/actions/workflows/test.yml/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/test.yml)
[![Build](https://github.com/CampbellTrevor/Amorsize/actions/workflows/build.yml/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/build.yml)
```

---

## Local Testing

Before pushing, you can test locally:

```bash
# Install dependencies
pip install pytest pytest-cov build twine

# Run tests
pytest -v --tb=short --cov=amorsize --cov-report=term-missing

# Build package
python -m build

# Verify package
twine check dist/*

# Test installation
pip install dist/*.whl
python -c "from amorsize import optimize; print('✓ Works')"
```

---

## Troubleshooting

**Tests fail on specific Python version:**
- Check if code uses features not available in that version
- Update code or adjust supported versions in pyproject.toml

**Build fails:**
- Verify pyproject.toml syntax
- Check MANIFEST.in includes all necessary files
- Ensure setup.py is compatible

**Publish fails:**
- Verify secrets are configured correctly
- Check PyPI API tokens are valid
- Ensure version number hasn't been published before

---

## Maintenance

**Update Python versions:**
Edit the matrix in `test.yml`:
```yaml
python-version: ['3.7', '3.8', '3.9', '3.10', '3.11', '3.12', '3.13']
```

**Update OS versions:**
Edit the matrix in `test.yml`:
```yaml
os: [ubuntu-latest, windows-latest, macos-latest]
```

**Update Actions versions:**
Check for updates at https://github.com/actions/
- `actions/checkout@v4`
- `actions/setup-python@v5`
- `actions/upload-artifact@v4`
