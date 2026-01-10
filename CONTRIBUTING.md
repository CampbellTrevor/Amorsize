# Contributing to Amorsize

Thank you for considering contributing to Amorsize! This document provides guidelines and information about the development workflow.

## Development Setup

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Amorsize.git
   cd Amorsize
   ```

2. **Install Development Dependencies**
   ```bash
   pip install -e ".[dev,full]"
   ```

3. **Run Tests Locally**
   ```bash
   pytest tests/ -v
   ```

## Continuous Integration (CI)

Amorsize uses GitHub Actions for automated testing and quality checks. All PRs automatically trigger:

### CI Workflow
- **Multi-version Testing**: Tests run on Python 3.7-3.13
- **Multi-platform Testing**: Ubuntu, macOS, and Windows
- **Code Coverage**: Coverage reports are generated and uploaded to Codecov
- **Package Building**: Validates that the package builds correctly
- **Code Quality**: Runs flake8 for basic linting

### Security Workflow
- **CodeQL Analysis**: Automated security scanning
- **Dependency Review**: Checks for vulnerable dependencies
- **Safety Check**: Scans for known security issues

### PR Checks
- **PR Title Validation**: Ensures conventional commit format
- **Quick Tests**: Runs core tests for fast feedback
- **Change Detection**: Identifies if tests were updated

### Scheduled Tests
- **Weekly Full Suite**: Runs comprehensive tests every Monday
- **Dependency Validation**: Ensures minimal and full installs work
- **Integration Examples**: Validates example scripts

## Making Changes

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write Tests**
   - Add tests for new features in `tests/`
   - Follow existing test patterns
   - Aim for high coverage

3. **Run Tests Locally**
   ```bash
   # Run all tests
   pytest tests/ -v
   
   # Run specific test file
   pytest tests/test_optimizer.py -v
   
   # Run with coverage
   pytest tests/ --cov=amorsize --cov-report=term
   ```

4. **Check Code Quality**
   ```bash
   # Basic syntax check
   flake8 amorsize --count --select=E9,F63,F7,F82 --show-source --statistics
   ```

5. **Commit Your Changes**
   - Use conventional commit format: `type: description`
   - Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore
   - Example: `feat: add support for custom timeout parameters`

6. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## CI Troubleshooting

### Test Failures
- **Local First**: Always run tests locally before pushing
- **Matrix Failures**: If tests fail on specific Python versions/OS, check the logs
- **Flaky Tests**: Multiprocessing tests can be timing-sensitive

### Build Failures
- **Package Build**: Ensure `pyproject.toml` is properly configured
- **Installation**: Test with `pip install -e .` locally

### Security Alerts
- **CodeQL**: Review security analysis results in the PR
- **Dependencies**: Update vulnerable dependencies promptly

## Release Process

Releases are automated through GitHub Actions:

1. **Create Release**: Use GitHub's release feature
2. **Automated Build**: Package is built and tested
3. **PyPI Upload**: Published to PyPI (requires secrets configuration)

## Testing Philosophy

Amorsize has comprehensive tests covering:
- **Core Functionality**: Optimizer, sampling, system detection
- **Edge Cases**: Empty data, unpicklable functions, memory constraints
- **Integration**: End-to-end workflows
- **Performance**: Expensive computational scenarios
- **Platform Compatibility**: Cross-platform and cross-version

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Check existing issues before creating new ones

## Code of Conduct

Be respectful, constructive, and collaborative. We're all here to make Amorsize better!
