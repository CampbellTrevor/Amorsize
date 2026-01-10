# GitHub Actions Workflows

This directory contains automated CI/CD workflows for the Amorsize project.

## Workflows

### 1. CI (`ci.yml`)
**Triggers:** Push, Pull Request, Manual

Comprehensive continuous integration testing across:
- **Python versions:** 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- **Operating systems:** Ubuntu, macOS, Windows
- **Dependency configurations:** With and without psutil

**Jobs:**
- `test`: Main test suite across all matrix combinations
- `test-minimal`: Validates functionality without optional dependencies
- `lint`: Code quality checks (flake8, mypy)
- `build`: Package building and installation verification
- `integration`: Integration tests and example script validation

**Key features:**
- Code coverage reporting (Codecov integration)
- Cross-platform compatibility validation
- Optional dependency testing

### 2. Release (`release.yml`)
**Triggers:** GitHub Release, Manual

Automated package building and publishing:

**Jobs:**
- `build`: Creates distribution packages (wheel + sdist)
- `test-package`: Validates built packages across platforms
- `publish-test-pypi`: Publishes to Test PyPI (manual trigger)
- `publish-pypi`: Publishes to PyPI (on release)

**Requirements:**
- GitHub environments: `test-pypi`, `pypi`
- Trusted publishing via OIDC (no tokens needed)

### 3. Scheduled Tests (`scheduled.yml`)
**Triggers:** Weekly (Mondays at 00:00 UTC), Manual

Proactive compatibility monitoring:

**Jobs:**
- `test-latest`: Tests with latest dependency versions
- `test-minimal-deps`: Validates minimum supported Python (3.7)
- `compatibility-check`: Verifies Python version requirements

**Features:**
- Automatic issue creation on failure
- Ensures forward compatibility with new releases

### 4. Documentation & Examples (`docs.yml`)
**Triggers:** Push/PR affecting docs or examples

Documentation and example validation:

**Jobs:**
- `validate-examples`: Syntax checking and quick execution tests
- `validate-readme`: Markdown linting and link checking
- `check-code-examples`: Validates Python code blocks in README

### 5. Security (`security.yml`)
**Triggers:** Push, Pull Request, Daily (2 AM UTC)

Security scanning and vulnerability detection:

**Jobs:**
- `codeql`: GitHub CodeQL analysis
- `dependency-review`: Checks for vulnerable dependencies (PRs only)
- `bandit`: Python security linting
- `safety`: Dependency vulnerability scanning

## Local Testing

### Run tests locally before pushing:
```bash
# Install dev dependencies
pip install -e ".[full,dev]"

# Run tests
pytest tests/ -v

# Run specific workflow jobs locally (requires act)
act -j test
act -j lint
```

### Validate workflows:
```bash
# Check workflow syntax
yamllint .github/workflows/*.yml

# Validate with actionlint
actionlint .github/workflows/*.yml
```

## Secrets and Configuration

### Required Secrets:
- `CODECOV_TOKEN`: For code coverage reporting (optional)

### GitHub Environments:
1. **test-pypi**
   - URL: https://test.pypi.org/p/amorsize
   - Trusted publishing configured

2. **pypi**
   - URL: https://pypi.org/p/amorsize
   - Trusted publishing configured
   - Protected: Requires approval for releases

## Workflow Status

| Workflow | Status | Purpose |
|----------|--------|---------|
| CI | ![CI](https://github.com/CampbellTrevor/Amorsize/workflows/CI/badge.svg) | Main test suite |
| Release | ![Release](https://github.com/CampbellTrevor/Amorsize/workflows/Release/badge.svg) | Package publishing |
| Security | ![Security](https://github.com/CampbellTrevor/Amorsize/workflows/Security/badge.svg) | Security scanning |
| Docs | ![Docs](https://github.com/CampbellTrevor/Amorsize/workflows/Documentation%20%26%20Examples/badge.svg) | Documentation validation |

## Maintenance

### Adding new Python version:
1. Add to matrix in `ci.yml`
2. Add classifier to `pyproject.toml`
3. Test locally if possible

### Updating dependencies:
1. Update `requirements.txt` or `pyproject.toml`
2. Let scheduled workflow catch any issues
3. Fix compatibility problems promptly

### Debugging failed workflows:
1. Check workflow run logs in GitHub Actions tab
2. Re-run failed jobs with debug logging
3. Test locally with same Python version/OS
4. Use `act` to simulate GitHub Actions locally

## Best Practices

1. **Always test locally first**: Run pytest before pushing
2. **Watch for deprecations**: Check workflow warnings
3. **Keep workflows fast**: Target < 10 minutes for CI
4. **Use caching wisely**: Dependencies are cached automatically
5. **Monitor security alerts**: Review Dependabot/CodeQL findings
6. **Keep documentation updated**: Update this README when changing workflows

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Python Package Publishing](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [CodeQL for Python](https://codeql.github.com/docs/codeql-language-guides/codeql-for-python/)
