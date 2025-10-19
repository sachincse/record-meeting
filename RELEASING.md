# Releasing to PyPI

Follow these steps to cut a release of `recordmymeeting` to TestPyPI or PyPI.

- Prerequisites
  - Python 3.8+
  - Build tools: `pip install -U build twine`
  - PyPI accounts/tokens for TestPyPI and/or PyPI

- Bump version
  - Edit `recordmymeeting/__init__.py` and set `__version__ = "X.Y.Z"`
  - Commit the change: `git add recordmymeeting/__init__.py && git commit -m "chore: release vX.Y.Z"`

- Clean old builds
  - Remove previous build artifacts if present:
    - `rm -rf dist build *.egg-info` (PowerShell: `Remove-Item dist,build,"*.egg-info" -Recurse -Force -ErrorAction SilentlyContinue`)

- Build the package
  - `python -m build`
  - Artifacts will appear in `dist/` (wheel and sdist)

- Verify the distribution
  - `python -m twine check dist/*`

- Upload to TestPyPI (recommended first)
  - `python -m twine upload --repository testpypi dist/*`
  - Install from TestPyPI in a clean env to verify:
    - `python -m venv .venv && .\.venv\Scripts\Activate.ps1`
    - `pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple recordmymeeting`
    - Sanity check:
      - `python -c "import recordmymeeting; print(recordmymeeting.__version__)"`
      - `recordmymeeting -h`

- Upload to PyPI (when satisfied)
  - `python -m twine upload dist/*`

- Tag the release
  - `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
  - `git push --tags`

- Post-release checklist
  - Update README if necessary
  - Open an issue to track any regressions or follow-ups
