# GitHub Actions Setup for Automated PyPI Releases

This guide explains how to set up automated PyPI releases using GitHub Actions.

## Overview

The GitHub Actions workflow (`.github/workflows/publish.yml`) automatically:
1. Runs tests on multiple Python versions
2. Builds the package (wheel and sdist)
3. Publishes to PyPI when you create a GitHub release

## Prerequisites

- GitHub repository for your project
- PyPI account at https://pypi.org
- Package ready for release (tests passing, version bumped)

## Setup Steps

### 1. Create PyPI API Token

1. **Log in to PyPI**: https://pypi.org/account/login/
2. **Go to Account Settings**: Click your username → "Account settings"
3. **Create API Token**:
   - Scroll to "API tokens" section
   - Click "Add API token"
   - Token name: `github-actions-recordmymeeting`
   - Scope: "Entire account" (or specific project after first upload)
   - Click "Add token"
4. **Copy the token**: It starts with `pypi-` and you'll only see it once!

### 2. Add Token to GitHub Secrets

1. **Go to your GitHub repository**
2. **Navigate to Settings** → **Secrets and variables** → **Actions**
3. **Click "New repository secret"**
4. **Add secret**:
   - Name: `PYPI_API_TOKEN`
   - Value: Paste your PyPI token (starts with `pypi-`)
   - Click "Add secret"

### 3. Create GitHub Release Environment (Optional but Recommended)

This adds an extra approval step before publishing:

1. **Go to Settings** → **Environments**
2. **Click "New environment"**
3. **Name**: `release`
4. **Configure environment**:
   - Check "Required reviewers" (optional)
   - Add yourself or team members as reviewers
   - Click "Save protection rules"

### 4. Verify Workflow File

Ensure `.github/workflows/publish.yml` exists in your repository with the correct content.

### 5. Test the Workflow

#### Option A: Create a GitHub Release (Recommended)

1. **Bump version** in `recordmymeeting/__init__.py`:
   ```python
   __version__ = "0.2.1"  # or your next version
   ```

2. **Commit and push**:
   ```bash
   git add recordmymeeting/__init__.py
   git commit -m "chore: bump version to 0.2.1"
   git push origin main
   ```

3. **Create a Git tag**:
   ```bash
   git tag -a v0.2.1 -m "Release v0.2.1"
   git push origin v0.2.1
   ```

4. **Create GitHub Release**:
   - Go to your repository on GitHub
   - Click "Releases" → "Create a new release"
   - Choose tag: `v0.2.1`
   - Release title: `v0.2.1`
   - Description: Copy from CHANGELOG.md
   - Click "Publish release"

5. **Monitor workflow**:
   - Go to "Actions" tab
   - Watch the workflow run
   - If environment protection is enabled, approve the deployment

#### Option B: Manual Trigger

1. **Go to Actions tab** in your repository
2. **Select "Publish to PyPI" workflow**
3. **Click "Run workflow"**
4. **Select branch** (usually `main`)
5. **Click "Run workflow"**

## Alternative: Trusted Publishing (More Secure)

Trusted Publishing eliminates the need for API tokens using OpenID Connect.

### Setup Trusted Publishing

1. **On PyPI**:
   - Go to your project page (after first manual upload)
   - Navigate to "Manage" → "Publishing"
   - Click "Add a new publisher"
   - Fill in:
     - PyPI Project Name: `recordmymeeting`
     - Owner: Your GitHub username
     - Repository: `recordmymeeting` (or your repo name)
     - Workflow: `publish.yml`
     - Environment: `release`
   - Click "Add"

2. **Update workflow file** (`.github/workflows/publish.yml`):
   - Remove the `password` line under "Publish to PyPI"
   - The workflow will use OIDC automatically

3. **Benefits**:
   - No API tokens to manage
   - More secure (short-lived credentials)
   - Automatic rotation

## Workflow Stages Explained

### Stage 1: Test
- Runs on Python 3.8, 3.9, 3.10, 3.11
- Installs dependencies
- Runs pytest test suite
- Must pass before building

### Stage 2: Build
- Builds wheel and source distribution
- Validates with `twine check`
- Uploads artifacts for publishing

### Stage 3: Publish
- Downloads build artifacts
- Publishes to PyPI using API token or trusted publishing
- Only runs after tests and build succeed

## Troubleshooting

### Workflow Fails at Test Stage
- Check test output in Actions logs
- Run tests locally: `pytest tests/ -v`
- Fix failing tests before releasing

### Workflow Fails at Publish Stage

**Error: Invalid or expired token**
- Regenerate PyPI API token
- Update `PYPI_API_TOKEN` secret in GitHub

**Error: File already exists**
- You're trying to upload the same version twice
- Bump version number in `recordmymeeting/__init__.py`
- Create a new release

**Error: 403 Forbidden**
- Check token has correct permissions
- For project-scoped tokens, ensure project exists on PyPI
- First upload must use account-scoped token

### Workflow Doesn't Trigger

- Ensure workflow file is in `.github/workflows/` directory
- Check you created a "Release" not just a tag
- Verify workflow file syntax (YAML is valid)

## Manual Release (Fallback)

If GitHub Actions fails, you can always release manually:

```bash
# Build
python -m build

# Check
python -m twine check dist/*

# Upload
python -m twine upload dist/*
```

## Security Best Practices

1. **Never commit API tokens** to the repository
2. **Use environment protection** for production releases
3. **Enable branch protection** on `main` branch
4. **Require pull request reviews** before merging
5. **Consider trusted publishing** over API tokens
6. **Rotate tokens periodically** (every 6-12 months)

## Release Checklist

Before creating a release:

- [ ] All tests pass locally
- [ ] Version bumped in `recordmymeeting/__init__.py`
- [ ] CHANGELOG.md updated
- [ ] README.md updated (if needed)
- [ ] Committed and pushed to `main`
- [ ] GitHub Actions secrets configured
- [ ] Created Git tag
- [ ] Created GitHub Release

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyPI Publishing Guide](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [PyPA GitHub Action](https://github.com/pypa/gh-action-pypi-publish)
