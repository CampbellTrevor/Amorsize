# GitHub Actions CI/CD Workflows

This directory contains GitHub Actions workflows for continuous integration and continuous deployment.

## Workflows

### 1. CI (`ci.yml`)
**Triggers:** Push/PR to `main` or `Iterate` branches, manual dispatch

**Purpose:** Comprehensive testing across multiple Python versions and operating systems

**Jobs:**
- **test**: Runs full test suite on Python 3.7-3.13 across Ubuntu, Windows, and macOS
- **test-minimal**: Tests minimal installation without optional dependencies (no psutil)
- **coverage**: Generates code coverage reports

**What it validates:**
- ✅ Package works on all supported Python versions (3.7-3.13)
- ✅ Package works on all major operating systems
- ✅ All 630+ tests pass
- ✅ Package works with and without optional dependencies
- ✅ Code coverage metrics

### 2. Code Quality (`code-quality.yml`)
**Triggers:** Push/PR to `main` or `Iterate` branches, manual dispatch

**Purpose:** Enforce code quality standards and best practices

**Jobs:**
- **lint**: Runs flake8 for PEP 8 compliance and code quality
- **type-check**: Runs mypy for static type checking

**What it validates:**
- ✅ No syntax errors or undefined names
- ✅ Code complexity within reasonable bounds
- ✅ PEP 8 style compliance (informational)
- ✅ Security vulnerabilities (bandit)
- ✅ Code formatting (black)
- ✅ Type hints correctness (informational)

### 3. Build (`build.yml`)
**Triggers:** Push/PR to `main` or `Iterate` branches, tags, manual dispatch

**Purpose:** Build and validate package distributions

**Jobs:**
- **build**: Creates source and wheel distributions
- **verify-install**: Tests installation on multiple platforms

**What it validates:**
- ✅ Package builds successfully (sdist and wheel)
- ✅ Distributions pass twine validation
- ✅ Wheel installs correctly on all platforms
- ✅ Source distribution installs correctly
- ✅ Basic functionality works after installation

**Artifacts:**
- Uploads built distributions (wheels and sdist) for inspection

### 4. Security (`security.yml`)
**Triggers:** Push/PR to `main` or `Iterate` branches, weekly schedule, manual dispatch

**Purpose:** Monitor security vulnerabilities in dependencies and code

**Jobs:**
- **security-scan**: Scans for known vulnerabilities using safety and bandit
- **dependency-review**: Reviews dependency changes in PRs

**What it validates:**
- ✅ No known security vulnerabilities in dependencies
- ✅ No security issues in code (SAST with bandit)
- ✅ Dependency changes don't introduce vulnerabilities

**Schedule:**
- Runs automatically every Monday at 00:00 UTC
- Also runs on every push/PR

## Viewing Results

### On GitHub
1. Navigate to the **Actions** tab in the repository
2. Select a workflow from the left sidebar
3. Click on a specific run to see details
4. View logs, artifacts, and test results

### Status Badges
Add these to README.md to show workflow status:

```markdown
![CI](https://github.com/CampbellTrevor/Amorsize/workflows/CI/badge.svg)
![Code Quality](https://github.com/CampbellTrevor/Amorsize/workflows/Code%20Quality/badge.svg)
![Build](https://github.com/CampbellTrevor/Amorsize/workflows/Build/badge.svg)
![Security](https://github.com/CampbellTrevor/Amorsize/workflows/Security/badge.svg)
```

## Running Locally

You can test GitHub Actions workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run CI workflow
act -j test

# Run specific job
act -j build
```

## Workflow Features

### Multi-Version Testing
- Tests Python 3.7 through 3.13
- Covers 3 major operating systems
- Total of 21 test matrix combinations

### Fail-Fast Disabled
- `fail-fast: false` ensures all matrix combinations run
- Helps identify platform-specific or version-specific issues

### Artifact Uploads
- Coverage reports preserved for analysis
- Built distributions saved for inspection
- Available for 90 days (GitHub default)

### Manual Triggers
- All workflows support `workflow_dispatch`
- Can be triggered manually from Actions tab
- Useful for testing before merging

## Maintenance

### Adding New Python Versions
When a new Python version is released:
1. Add it to the matrix in `ci.yml`
2. Add the classifier to `pyproject.toml`
3. Update this documentation

### Updating Dependencies
Actions are pinned to major versions (e.g., `@v4`):
- `actions/checkout@v4` - Repository checkout
- `actions/setup-python@v5` - Python installation
- `actions/upload-artifact@v4` - Artifact uploads
- `actions/download-artifact@v4` - Artifact downloads

Check for updates periodically using Dependabot.

## Troubleshooting

### Test Failures
1. Check the job logs in GitHub Actions
2. Look for platform-specific or version-specific patterns
3. Run tests locally with the failing Python version

### Build Failures
1. Verify `pyproject.toml` syntax
2. Check that all required files are included in MANIFEST.in
3. Test build locally: `python -m build`

### Workflow Syntax Errors
1. Validate YAML syntax: `yamllint .github/workflows/*.yml`
2. Use GitHub's workflow editor (has built-in validation)
3. Check action versions are still available

## Future Enhancements

Potential additions for future iterations:
- [ ] Automated PyPI publishing on releases
- [ ] Benchmark performance regression testing
- [ ] Documentation building and deployment
- [ ] Automated changelog generation
- [ ] Issue/PR templates
- [ ] Automated dependency updates (Dependabot)
- [ ] Code coverage tracking with codecov.io
- [ ] Pre-commit hooks configuration
