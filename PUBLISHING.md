# PyPI Publication Guide for Amorsize

This document describes how to publish Amorsize to PyPI using the automated CI/CD workflow.

## Prerequisites

### 1. PyPI Account Setup

1. Create an account on [PyPI](https://pypi.org/account/register/)
2. Create an account on [Test PyPI](https://test.pypi.org/account/register/) for testing

### 2. PyPI Trusted Publishing (Recommended)

Amorsize uses **PyPI Trusted Publishing** which eliminates the need for API tokens. This is the most secure method.

**Setup Steps:**

1. Go to your PyPI account settings: https://pypi.org/manage/account/publishing/
2. Add a new "pending publisher":
   - **PyPI Project Name**: `amorsize`
   - **Owner**: `CampbellTrevor`
   - **Repository name**: `Amorsize`
   - **Workflow name**: `publish.yml`
   - **Environment name**: (leave blank)

3. Repeat for Test PyPI: https://test.pypi.org/manage/account/publishing/

**Note**: The first time you publish, PyPI will automatically create the project and associate it with the GitHub repository.

### 3. Alternative: API Token Method (Fallback)

If trusted publishing doesn't work, use API tokens:

1. Generate an API token on [PyPI](https://pypi.org/manage/account/token/)
2. Add it to GitHub repository secrets as `PYPI_API_TOKEN`
3. Generate a token on [Test PyPI](https://test.pypi.org/manage/account/token/)
4. Add it to GitHub repository secrets as `TEST_PYPI_API_TOKEN`

To use tokens, modify `.github/workflows/publish.yml`:
```yaml
- name: Publish to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    password: ${{ secrets.PYPI_API_TOKEN }}  # Add this line
```

## Publication Methods

### Method 1: Automated Release (Recommended)

**Triggered by**: Creating a new Git tag with semantic versioning

```bash
# Ensure you're on the main branch
git checkout main
git pull origin main

# Update version in pyproject.toml
# Edit the version field, e.g., "0.1.0" -> "0.1.1"

# Commit version bump
git add pyproject.toml
git commit -m "Bump version to 0.1.1"
git push origin main

# Create and push tag
git tag -a v0.1.1 -m "Release version 0.1.1"
git push origin v0.1.1
```

**What happens:**
1. GitHub Actions workflow triggers on tag push
2. Runs full test suite (689 tests)
3. Validates package with `check-manifest` and `twine`
4. Builds source distribution and wheel
5. Publishes to PyPI (production)
6. Creates a GitHub Release with artifacts
7. Tests installation from PyPI

### Method 2: Manual Dispatch (Testing)

**Triggered by**: Manual workflow run from GitHub Actions UI

**Use cases:**
- Testing publication to Test PyPI
- Emergency releases
- Testing the publication workflow

**Steps:**

1. Go to: https://github.com/CampbellTrevor/Amorsize/actions/workflows/publish.yml
2. Click "Run workflow"
3. Select branch (usually `main`)
4. Choose target:
   - Check "Publish to Test PyPI" for testing
   - Uncheck to publish to production PyPI
5. Click "Run workflow"

**What happens:**
- Same validation and build steps
- Publishes to Test PyPI or production based on selection
- Does NOT create a GitHub Release (manual only)

## Pre-Release Checklist

Before publishing a new version, ensure:

- [ ] **All tests pass**: `pytest tests/ -v`
- [ ] **Version bumped**: Update `version` in `pyproject.toml`
- [ ] **CHANGELOG updated**: Document changes in `CHANGELOG.md`
- [ ] **Documentation current**: README.md reflects new features
- [ ] **No uncommitted changes**: `git status` shows clean tree
- [ ] **Main branch up-to-date**: `git pull origin main`
- [ ] **Build successful**: `python -m build` completes without errors
- [ ] **Package valid**: `twine check dist/*` passes
- [ ] **CI workflows passing**: All GitHub Actions checks green

## Version Numbering

Amorsize follows [Semantic Versioning](https://semver.org/):

- **Major version** (X.0.0): Breaking API changes
- **Minor version** (0.X.0): New features, backward compatible
- **Patch version** (0.0.X): Bug fixes, backward compatible

**Examples:**
- `0.1.0` → `0.1.1`: Bug fixes
- `0.1.1` → `0.2.0`: New features (e.g., new optimizer mode)
- `0.2.0` → `1.0.0`: API breaking changes or production-ready declaration

## Post-Publication Verification

After publishing, verify the release:

### 1. Check PyPI Page
Visit: https://pypi.org/project/amorsize/

Verify:
- [ ] Correct version displayed
- [ ] README renders correctly
- [ ] Metadata (description, keywords, classifiers) correct
- [ ] Installation instructions work

### 2. Test Installation

```bash
# In a clean virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from PyPI
pip install amorsize

# Verify import
python -c "from amorsize import optimize; print('Success!')"

# Test basic functionality
python -c "
from amorsize import optimize

def test_func(x):
    return x ** 2

result = optimize(test_func, range(100))
print(f'Recommended: n_jobs={result.n_jobs}, chunksize={result.chunksize}')
"
```

### 3. Test Optional Dependencies

```bash
# Test with full dependencies
pip install amorsize[full]
python -c "from amorsize import optimize; print('Full install OK')"

# Test Bayesian optimization
pip install amorsize[bayesian]
python -c "from amorsize import bayesian_tune_parameters; print('Bayesian install OK')"
```

## Troubleshooting

### Issue: "Project name already exists"
**Cause**: Package name taken on PyPI
**Solution**: Choose a different package name in `pyproject.toml`

### Issue: "Version already exists"
**Cause**: Version already published to PyPI
**Solution**: Bump version in `pyproject.toml` and create new tag

### Issue: "Trusted publishing authentication failed"
**Cause**: Trusted publishing not set up correctly
**Solution**: 
1. Verify repository settings on PyPI
2. Check workflow name matches exactly
3. Ensure workflow has `id-token: write` permission

### Issue: "Tests fail in CI"
**Cause**: Code issues or environment problems
**Solution**: Fix failing tests before publishing:
```bash
pytest tests/ -v --tb=short
```

### Issue: "Package build fails"
**Cause**: Missing files or incorrect manifest
**Solution**: Run locally to debug:
```bash
python -m build
check-manifest
twine check dist/*
```

## Rolling Back a Release

If you need to yank (hide) a release on PyPI:

```bash
# Install twine
pip install twine

# Yank the release (keeps it available but hidden)
twine upload --repository-url https://pypi.org/ --skip-existing --yank "Reason for yanking" dist/*

# Or use PyPI web interface:
# 1. Log into PyPI
# 2. Go to project settings
# 3. Find the version
# 4. Click "Options" -> "Yank release"
```

**Note**: You cannot delete a version on PyPI once published. Yanking is the recommended approach.

## Best Practices

1. **Test on Test PyPI first**: Always test with Test PyPI before production
2. **Increment versions carefully**: Never reuse version numbers
3. **Keep CHANGELOG current**: Document all changes for users
4. **Tag releases consistently**: Use `vX.Y.Z` format
5. **Monitor downloads**: Check PyPI stats regularly
6. **Respond to issues**: Monitor GitHub issues for user feedback
7. **Security updates**: Apply security patches promptly

## Resources

- [PyPI Documentation](https://packaging.python.org/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Actions PyPI Publish](https://github.com/marketplace/actions/pypi-publish)
- [Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
- [Python Packaging User Guide](https://packaging.python.org/en/latest/)

## Support

For questions or issues with publishing:
1. Check this guide
2. Review GitHub Actions logs
3. Consult PyPI documentation
4. Open an issue on GitHub
