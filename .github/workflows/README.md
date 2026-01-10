# GitHub Actions Workflows

This directory contains CI/CD workflows for the Amorsize project.

## Workflows

### 1. Tests (`test.yml`)
**Triggers:** Push to main/Iterate/copilot branches, Pull Requests

Runs comprehensive test suite across multiple platforms and Python versions:
- **Operating Systems:** Ubuntu, Windows, macOS
- **Python Versions:** 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- **Features:**
  - Installs package with dev and full dependencies
  - Runs pytest with coverage reporting
  - Uploads coverage to Codecov (Ubuntu + Python 3.12)

**Status Badge:**
```markdown
![Tests](https://github.com/CampbellTrevor/Amorsize/workflows/Tests/badge.svg)
```

### 2. Build (`build.yml`)
**Triggers:** Push to main/Iterate/copilot branches, Pull Requests, Releases

Validates package building and distribution:
- Builds source distribution and wheel
- Validates package with twine
- Tests installation from wheel
- Stores artifacts for 30 days

**Status Badge:**
```markdown
![Build](https://github.com/CampbellTrevor/Amorsize/workflows/Build/badge.svg)
```

### 3. Quick Check (`quick-check.yml`)
**Triggers:** Push to copilot branches, Pull Requests

Fast feedback workflow for rapid iteration:
- Runs on Python 3.12 + Ubuntu only
- Quick test suite execution with fail-fast
- Verifies core imports work

### 4. Publish to PyPI (`publish.yml`)
**Triggers:** Release published, Manual workflow dispatch

Publishes package to PyPI:
- Uses trusted publisher (OIDC) authentication
- Builds and publishes automatically on release
- Can be triggered manually for testing

## Setup Requirements

### Codecov (Optional)
To enable coverage reporting to Codecov:
1. Sign up at https://codecov.io/
2. Add repository to Codecov
3. Add `CODECOV_TOKEN` to repository secrets

### PyPI Publishing
To enable PyPI publishing:
1. Configure PyPI trusted publisher at https://pypi.org/
2. Add the repository and workflow details
3. No token needed (uses OIDC)

## Workflow Matrix

| Workflow | OS | Python | Coverage | Artifacts |
|----------|------|---------|----------|-----------|
| Tests | Ubuntu, Windows, macOS | 3.7-3.13 | ✓ | - |
| Build | Ubuntu | 3.12 | - | ✓ |
| Quick Check | Ubuntu | 3.12 | - | - |
| Publish | Ubuntu | 3.12 | - | ✓ |

## Local Testing

Test workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
# macOS: brew install act
# Linux: Check https://github.com/nektos/act

# Run quick check
act -j quick-test

# Run build
act -j build

# Run test matrix (requires Docker)
act -j test
```

## Branch Protection

Recommended branch protection rules for `main` and `Iterate`:
- ✓ Require Tests workflow to pass
- ✓ Require Build workflow to pass
- ✓ Require status checks to be up to date
- ✓ Require branches to be up to date before merging

## Performance

| Workflow | Typical Duration | Resource Usage |
|----------|------------------|----------------|
| Quick Check | ~30 seconds | 1 runner |
| Build | ~1-2 minutes | 1 runner |
| Tests (full matrix) | ~5-10 minutes | 19 runners |
| Publish | ~1-2 minutes | 1 runner |

## Maintenance

### Updating Python Versions
When new Python versions are released:
1. Update `matrix.python-version` in `test.yml`
2. Update classifiers in `pyproject.toml`
3. Test locally before merging

### Updating Actions
GitHub Actions are pinned to major versions (v4, v5).
Check for updates periodically:
- `actions/checkout@v4`
- `actions/setup-python@v5`
- `actions/upload-artifact@v4`
- `codecov/codecov-action@v4`
- `pypa/gh-action-pypi-publish@release/v1`
