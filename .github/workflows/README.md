# GitHub Actions CI/CD Workflows

This directory contains automated workflows for continuous integration and deployment of the Amorsize library.

## Workflows

### 1. Tests (`test.yml`)
**Trigger:** Push and Pull Requests to `main` and `Iterate` branches

**Jobs:**
- **test**: Comprehensive testing across multiple Python versions (3.7-3.13) and operating systems (Ubuntu, Windows, macOS)
- **test-minimal**: Tests without optional `psutil` dependency to ensure core functionality works
- **coverage**: Generates code coverage reports using pytest-cov

**Key Features:**
- Matrix testing: 21 combinations of Python versions and OS platforms
- Dependency caching for faster builds
- Separate quick test runs excluding slow markers
- Coverage artifacts uploaded for 30 days

### 2. Build (`build.yml`)
**Trigger:** Push and Pull Requests to `main` and `Iterate` branches

**Jobs:**
- **build**: Builds package using modern `python -m build` (PEP 517/518)
- **build-legacy**: Validates backward compatibility with `setup.py`
- **check-manifest**: Verifies package manifest completeness

**Key Features:**
- Modern PEP 517/518 build process
- Legacy setup.py compatibility validation
- Package structure verification with twine
- Installation testing of built wheels
- Build artifacts uploaded for 30 days

### 3. Lint (`lint.yml`)
**Trigger:** Push and Pull Requests to `main` and `Iterate` branches

**Jobs:**
- **ruff**: Modern, fast Python linter (check and format)
- **type-check**: Type checking with mypy
- **imports**: Import order validation with isort
- **security**: Security scanning with bandit

**Key Features:**
- Fast linting with Ruff
- Type safety checking
- Security vulnerability detection
- Advisory mode (doesn't fail build, provides feedback)

## Usage

### Running Locally
You can test workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
# macOS: brew install act
# Linux: see https://github.com/nektos/act#installation

# Test the test workflow
act -j test

# Test the build workflow
act -j build

# List all available jobs
act -l
```

### Manual Trigger
All workflows support manual triggering via GitHub Actions UI:
1. Go to Actions tab in the repository
2. Select the workflow
3. Click "Run workflow"

### Skipping CI
Add `[skip ci]` to your commit message to skip workflow runs:
```bash
git commit -m "docs: update README [skip ci]"
```

## Test Strategy

### Python Version Coverage
- **3.7**: Minimum supported version (legacy support)
- **3.8-3.12**: Mainstream versions with full testing
- **3.13**: Latest version (forward compatibility)

### Operating System Coverage
- **Ubuntu**: Primary Linux testing
- **Windows**: Windows-specific behavior validation
- **macOS**: Apple Silicon and Intel compatibility

### Test Categories
1. **Full tests**: All tests including slow performance benchmarks
2. **Quick tests**: Excluding `@pytest.mark.slow` for fast feedback
3. **Minimal tests**: Without psutil to validate core functionality
4. **Coverage**: Code coverage measurement and reporting

## Badge Status
Add these badges to your README.md:

```markdown
![Tests](https://github.com/CampbellTrevor/Amorsize/workflows/Tests/badge.svg)
![Build](https://github.com/CampbellTrevor/Amorsize/workflows/Build/badge.svg)
![Lint](https://github.com/CampbellTrevor/Amorsize/workflows/Lint/badge.svg)
```

## Maintenance

### Adding New Python Versions
Edit the `matrix.python-version` in `test.yml`:
```yaml
matrix:
  python-version: ['3.7', '3.8', '3.9', '3.10', '3.11', '3.12', '3.13', '3.14']
```

### Adding New Linters
Add new jobs to `lint.yml` following the existing pattern:
```yaml
new-linter:
  name: New Linter
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
    - run: pip install new-linter
    - run: new-linter check
```

### Modifying Test Matrix
Exclude specific combinations in `test.yml`:
```yaml
exclude:
  - os: macos-latest
    python-version: '3.7'
```

## Performance Considerations

### Caching
- Pip dependencies are cached using `cache: 'pip'` in setup-python action
- Reduces installation time by ~30-60 seconds per job

### Parallelization
- Test matrix runs in parallel (21 jobs for full matrix)
- Build and lint jobs also run in parallel
- Total CI time: ~5-10 minutes

### Resource Usage
- Each test job uses ~2-4 minutes
- Build jobs use ~2-3 minutes
- Lint jobs use ~1-2 minutes
- Coverage job uses ~3-5 minutes

## Artifacts

### Coverage Reports
- **Retention**: 30 days
- **Format**: XML (Cobertura)
- **Location**: Uploaded to workflow run artifacts
- **Usage**: Download and analyze locally or integrate with coverage services

### Build Distributions
- **Retention**: 30 days
- **Contents**: Wheel and source distributions
- **Usage**: Download for manual testing or publishing

### Security Scans
- **Retention**: 30 days
- **Format**: JSON
- **Contents**: Bandit security analysis results
- **Usage**: Review security findings

## Troubleshooting

### Test Failures
1. Check the workflow run logs in GitHub Actions
2. Look for specific test failures in the matrix
3. Reproduce locally: `pytest tests/ -v`

### Build Failures
1. Verify pyproject.toml syntax
2. Check MANIFEST.in includes all necessary files
3. Test locally: `python -m build`

### Lint Issues
All lint jobs are advisory and won't fail the build. They provide feedback for improvement:
- Ruff: Code style and common errors
- Mypy: Type checking issues
- Isort: Import order problems
- Bandit: Security vulnerabilities

### Platform-Specific Issues
- **macOS arm64**: Python 3.7 not available, excluded from matrix
- **Windows**: Path separators may differ, tests handle this
- **Linux**: Primary development and testing platform

## Integration

### Pull Request Checks
All workflows run on pull requests and must pass before merging:
- ✅ Tests pass on all supported Python versions
- ✅ Package builds successfully
- ℹ️ Lint feedback provided (advisory)

### Branch Protection
Recommended branch protection rules:
- Require status checks to pass before merging
- Required checks: `Test Python 3.11 on ubuntu-latest`, `Build Package`
- Optional checks: All other test matrix jobs

## Future Enhancements

### Potential Additions
1. **Publish Workflow**: Automated PyPI publishing on release
2. **Documentation**: Sphinx documentation building and deployment
3. **Benchmark Tracking**: Performance regression detection
4. **Dependency Updates**: Automated dependency update PRs (Dependabot)
5. **Release Automation**: Automated changelog and release notes

### Coverage Integration
Consider integrating with coverage services:
- Codecov: https://codecov.io/
- Coveralls: https://coveralls.io/
- CodeClimate: https://codeclimate.com/

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [actions/setup-python](https://github.com/actions/setup-python)
- [actions/checkout](https://github.com/actions/checkout)
- [actions/upload-artifact](https://github.com/actions/upload-artifact)
- [pytest Documentation](https://docs.pytest.org/)
- [Python Build Documentation](https://build.pypa.io/)
