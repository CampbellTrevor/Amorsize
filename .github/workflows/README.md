# GitHub Actions CI/CD Workflows

This directory contains automated workflows for continuous integration and deployment.

## Workflows

### 1. Test Suite (`test.yml`)

Runs comprehensive tests across multiple Python versions and operating systems.

**Triggers:**
- Push to `main` or `Iterate` branches
- Pull requests to `main` or `Iterate` branches

**Matrix Testing:**
- **Operating Systems:** Ubuntu, macOS, Windows
- **Python Versions:** 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- **Total Jobs:** 21 test combinations (3 OS × 7 Python versions)

**Additional Tests:**
- Fallback testing without `psutil` (validates graceful degradation)
- Coverage reporting with HTML report upload

**Artifacts:**
- `coverage-report`: HTML coverage report

**Duration:** ~15-20 minutes (parallel execution)

### 2. Build Package (`build.yml`)

Verifies that the package builds correctly and can be installed.

**Triggers:**
- Push to `main` or `Iterate` branches
- Pull requests to `main` or `Iterate` branches

**Steps:**
1. Build wheel distribution (`.whl`)
2. Build source distribution (`.tar.gz`)
3. Install wheel and verify imports
4. Test with optional dependencies

**Artifacts:**
- `wheel`: Built wheel package
- `sdist`: Source distribution

**Duration:** ~2-3 minutes

## Viewing Results

### In Pull Requests
All workflow runs will appear as status checks on pull requests. Click "Details" to see logs.

### In GitHub Actions Tab
Navigate to **Actions** tab in the repository to see all workflow runs, including:
- Status (success/failure)
- Logs for each job
- Downloadable artifacts

## Downloading Artifacts

Artifacts are available for 90 days after workflow completion:
1. Go to the **Actions** tab
2. Click on a workflow run
3. Scroll to **Artifacts** section
4. Download available artifacts (wheels, coverage reports, etc.)

## Local Testing

To test locally before pushing:

```bash
# Run tests (matching CI)
pytest tests/ -v --tb=short

# Run tests with coverage
pytest tests/ --cov=amorsize --cov-report=html

# Build package (matching CI)
pip install build
python -m build

# Install and test wheel
pip install dist/amorsize-*.whl
python -c "from amorsize import optimize; print('✓ Import successful')"
```

## Workflow Maintenance

### Updating Python Versions
Edit the `matrix.python-version` array in `test.yml`:
```yaml
python-version: ['3.7', '3.8', '3.9', '3.10', '3.11', '3.12', '3.13', '3.14']
```

### Updating OS
Edit the `matrix.os` array in `test.yml`:
```yaml
os: [ubuntu-latest, macos-latest, windows-latest]
```

### Updating Actions
GitHub Actions are pinned to major versions (e.g., `v4`, `v5`):
- `actions/checkout@v4` - Latest v4.x
- `actions/setup-python@v5` - Latest v5.x
- `actions/upload-artifact@v4` - Latest v4.x

These automatically receive minor updates and security patches.

## Troubleshooting

### Tests Fail on Specific Python Version
Check the logs for that specific job. Common issues:
- Dependency compatibility
- Syntax changes between Python versions
- Platform-specific behavior

### Tests Fail on Specific OS
Check the logs for that specific OS. Common issues:
- Path separators (Windows vs Unix)
- File permissions
- Platform-specific dependencies

### Build Fails
Common issues:
- Missing files in MANIFEST.in
- Import errors (packaging issue)
- Dependency version conflicts

### Artifacts Not Available
Artifacts are only uploaded on successful workflow completion. Check logs if missing.

## Future Enhancements

Potential workflow additions:
- **Lint workflow:** Code quality checks (if linters added)
- **Publish workflow:** Automated PyPI releases on tags
- **Docs workflow:** Build and deploy documentation
- **Benchmark workflow:** Performance regression testing
- **Dependency updates:** Automated Dependabot PRs
