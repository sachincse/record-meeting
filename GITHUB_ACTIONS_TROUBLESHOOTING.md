# GitHub Actions Troubleshooting Guide

Common issues and solutions for the GitHub Actions workflow.

## Issue 1: Environment "release" Not Found

**Error Message:**
```
Error: The environment 'release' was not found
```

**Solution:**
The workflow is now fixed - the `environment: release` line is commented out. If you want to use environment protection:

1. Go to your repository → **Settings** → **Environments**
2. Click **New environment**
3. Name it `release`
4. (Optional) Add protection rules
5. Uncomment line 70 in `.github/workflows/publish.yml`

## Issue 2: PyAudio Installation Fails

**Error Message:**
```
error: command 'gcc' failed
fatal error: portaudio.h: No such file or directory
```

**Solution:**
✅ **Already fixed!** The workflow now installs system dependencies:
```yaml
- name: Install system dependencies
  run: |
    sudo apt-get update
    sudo apt-get install -y portaudio19-dev python3-pyaudio
```

## Issue 3: Tests Fail in CI

**Error Message:**
```
ImportError: No module named 'recordmymeeting'
ModuleNotFoundError: No module named 'recordmymeeting'
```

**Solution:**
Check that `pip install -e .` runs successfully. The workflow installs the package in editable mode before running tests.

## Issue 4: PYPI_API_TOKEN Not Found

**Error Message:**
```
Error: Input required and not supplied: password
```

**Solution:**
1. Go to https://pypi.org/manage/account/token/
2. Create a new API token
3. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
4. Add secret named `PYPI_API_TOKEN` with your token value

## Issue 5: Workflow Doesn't Trigger

**Problem:** Workflow doesn't run when you create a release

**Solution:**
The workflow triggers on:
- **GitHub Release**: Create a release (not just a tag)
- **Manual**: Go to Actions → "Publish to PyPI" → "Run workflow"

To create a release:
1. Go to https://github.com/sachincse/recordmymeeting/releases
2. Click "Create a new release"
3. Choose or create a tag (e.g., `v0.2.0`)
4. Fill in title and description
5. Click "Publish release"

## Issue 6: Build Fails - Missing Files

**Error Message:**
```
error: [Errno 2] No such file or directory: 'README.md'
```

**Solution:**
Ensure all required files are committed:
```bash
git add README.md setup.py pyproject.toml recordmymeeting/ tests/
git commit -m "Add all required files"
git push
```

## Issue 7: Permission Denied on PyPI Upload

**Error Message:**
```
403 Client Error: Forbidden
```

**Solutions:**

**A. First-time upload:**
- You need to upload manually first, then use GitHub Actions
- Or use an account-scoped token (not project-scoped)

**B. Token expired:**
- Regenerate token on PyPI
- Update GitHub secret

**C. Wrong repository:**
- Ensure you're uploading to the correct PyPI account

## Issue 8: Version Already Exists

**Error Message:**
```
400 Client Error: File already exists
```

**Solution:**
You cannot re-upload the same version. Bump the version:

1. Edit `recordmymeeting/__init__.py`:
   ```python
   __version__ = "0.2.1"  # Increment version
   ```

2. Update `CHANGELOG.md`

3. Commit and create new release with new tag

## Issue 9: Tests Pass Locally But Fail in CI

**Common causes:**

1. **Missing dependencies in requirements-dev.txt**
   ```bash
   # Add to requirements-dev.txt
   pytest>=7.0.0
   ```

2. **Platform-specific code**
   - Tests might work on Windows but fail on Linux
   - Check for OS-specific paths or commands

3. **Hardware dependencies**
   - Our tests avoid hardware, but double-check
   - Mock any hardware-dependent code

## Quick Fixes

### Re-run Failed Workflow
1. Go to Actions tab
2. Click on failed workflow
3. Click "Re-run all jobs"

### View Detailed Logs
1. Go to Actions tab
2. Click on workflow run
3. Click on failed job (test/build/publish)
4. Expand each step to see logs

### Test Workflow Locally

You can test the workflow steps locally:

```bash
# Test stage
python -m pip install --upgrade pip
pip install -e .
pip install -r requirements-dev.txt
pytest tests/ -v

# Build stage
pip install build twine
python -m build
twine check dist/*
```

## Manual Release (Bypass GitHub Actions)

If GitHub Actions continues to fail, you can release manually:

```bash
# Build
python -m build

# Check
python -m twine check dist/*

# Upload to PyPI
python -m twine upload dist/*
```

## Getting Help

If you're still stuck:

1. **Check workflow logs**: Actions tab → Click on run → View logs
2. **Copy error message**: Share the exact error
3. **Check GitHub Actions status**: https://www.githubstatus.com/
4. **PyPI status**: https://status.python.org/

## Workflow File Location

The workflow file is at:
```
.github/workflows/publish.yml
```

Any changes to this file require a commit and push to take effect.

## Common Commands

```bash
# View workflow status
# Go to: https://github.com/sachincse/recordmymeeting/actions

# Manually trigger workflow
# Go to: Actions → "Publish to PyPI" → "Run workflow"

# Check secrets
# Go to: Settings → Secrets and variables → Actions

# View environments
# Go to: Settings → Environments
```

## Success Indicators

A successful workflow run will show:
- ✅ Test (all Python versions)
- ✅ Build
- ✅ Publish
- Package appears on PyPI: https://pypi.org/project/recordmymeeting/

## Next Steps After Fixing

1. Commit the fixed workflow
2. Push to GitHub
3. Create a new release or manually trigger workflow
4. Monitor the Actions tab
5. Verify package on PyPI
