# GitHub Actions Workflows

This directory contains automated workflows for continuous integration, building, and quality assurance.

## Workflows

### ci.yml - Continuous Integration
**Purpose:** Automated testing across multiple Python versions and platforms

**Runs on:**
- Push to main, Iterate, or develop branches
- Pull requests to main, Iterate, or develop branches
- Manual trigger (workflow_dispatch)

**What it does:**
- Tests Python 3.7-3.13 on Linux, macOS, and Windows (20+ configurations)
- Tests with and without optional psutil dependency
- Runs full test suite (630+ tests)
- Validates CLI functionality
- Tests basic imports and API

**Duration:** ~10-15 minutes for full matrix

### build.yml - Package Building
**Purpose:** Automated package building and distribution validation

**Runs on:**
- Push to main or Iterate branches
- Pull requests to main or Iterate branches
- Git tags matching 'v*' (for releases)
- Manual trigger (workflow_dispatch)

**What it does:**
- Builds wheel and source distributions
- Validates packages with twine
- Tests installation on Linux, macOS, and Windows
- Verifies all public APIs work after installation
- Uploads build artifacts

**Duration:** ~5-7 minutes

### lint.yml - Code Quality
**Purpose:** Code quality and style consistency checks

**Runs on:**
- Push to main, Iterate, or develop branches
- Pull requests to main, Iterate, or develop branches
- Manual trigger (workflow_dispatch)

**What it does:**
- Checks for syntax errors and undefined names (strict)
- Validates code formatting with black (informational)
- Validates import sorting with isort (informational)
- Checks code complexity limits

**Duration:** ~1-2 minutes

## Viewing Results

1. Go to the repository on GitHub
2. Click the "Actions" tab
3. Select a workflow to see its runs
4. Click on a specific run to see detailed logs

**Status Indicators:**
- ✅ Green checkmark = All checks passed
- ❌ Red X = Some checks failed (click for details)
- 🟡 Yellow dot = Workflow in progress

## Manual Triggering

All workflows support manual triggering:

1. Go to Actions tab
2. Select the workflow (CI, Build, or Lint)
3. Click "Run workflow" button
4. Select the branch
5. Click "Run workflow"

## Workflow Configuration

All workflows use:
- Latest GitHub Actions (checkout@v4, setup-python@v5)
- Modern Python versions (3.7-3.13)
- Cross-platform testing (Linux, macOS, Windows)
- Fail-safe strategy (continue on failures to see all results)

## Maintenance

**When to update workflows:**
- Adding new Python version support
- Changing test infrastructure
- Adding new dependencies that need validation
- Modifying package build process
- Adding new quality checks

**Testing workflow changes:**
- Create a PR with workflow changes
- Workflows will run on the PR branch
- Verify results before merging

## Integration with Development

**For Contributors:**
- Workflows run automatically on PRs
- Green checkmarks = your PR is good to merge
- Red X = fix the issues before merge
- Click on failed checks for details

**For Maintainers:**
- All PRs automatically validated
- Can require passing checks before merge
- Artifacts available for inspection
- Cross-platform issues caught early

## Future Enhancements

Planned workflow additions:
- PyPI publication workflow (on git tags)
- Code coverage reporting (Codecov integration)
- Performance regression testing
- Automated changelog generation
- Dependency security scanning

---

**Last Updated:** Iteration 40
**Workflows Count:** 3 (CI, Build, Lint)
**Test Configurations:** 26+ per run
