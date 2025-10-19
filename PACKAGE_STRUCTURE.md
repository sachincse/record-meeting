# RecordMyMeeting - Package Structure

This document describes the final structure of the `recordmymeeting` PyPI package.

## Directory Structure

```
record-meeting/
├── .github/
│   └── workflows/
│       └── publish.yml      # GitHub Actions release workflow
├── recordmymeeting/         # Main package
│   ├── __init__.py          # Package init, exports RecordMyMeeting
│   ├── cli.py               # CLI entry point
│   ├── core.py              # Core recording logic
│   ├── device_manager.py    # Audio device detection
│   ├── gui_app.py           # GUI application
│   └── utils.py             # Utility functions
├── tests/                   # Test suite
│   ├── test_cli.py          # CLI import tests
│   ├── test_core.py         # Core functionality tests
│   └── test_device_manager.py  # Device detection tests
├── docs/                    # Documentation
│   ├── API.md               # Python API reference
│   ├── CLI_GUIDE.md         # Command-line guide
│   └── GUI_GUIDE.md         # GUI tutorial
├── .gitignore               # Git ignore patterns
├── CHANGELOG.md             # Version history
├── CONTRIBUTING.md          # Contribution guidelines
├── GITHUB_ACTIONS_SETUP.md  # Automated release setup
├── LEGAL_COMPLIANCE.md      # Recording laws & best practices
├── PACKAGE_STRUCTURE.md     # This file
├── README.md                # Main documentation
├── RELEASING.md             # Manual PyPI release guide
├── pyproject.toml           # Build system config
├── setup.py                 # Package metadata
├── requirements.txt         # Runtime dependencies
└── requirements-dev.txt     # Development dependencies
```

## Documentation Overview

### For Users
- **README.md** - Start here
- **docs/CLI_GUIDE.md** - Command-line usage
- **docs/GUI_GUIDE.md** - GUI usage
- **docs/API.md** - Python API
- **LEGAL_COMPLIANCE.md** - Recording laws

### For Contributors
- **CONTRIBUTING.md** - How to contribute
- **CHANGELOG.md** - Version history
- **tests/** - Test suite

### For Maintainers
- **RELEASING.md** - Manual release process
- **GITHUB_ACTIONS_SETUP.md** - Automated releases
- **setup.py** - Package configuration
- **pyproject.toml** - Build system

## Key Files

### README.md
- Project overview with badges
- Feature list
- Installation instructions
- Quick start examples
- Links to all documentation
- Legal compliance notice

### Documentation (docs/)

**API.md**
- Complete Python API reference
- RecordMyMeeting class documentation
- Device manager functions
- Code examples

**CLI_GUIDE.md**
- Complete command-line reference
- All flags and options
- Usage examples
- Output structure
- Tips and troubleshooting

**GUI_GUIDE.md**
- GUI feature overview
- Usage examples
- Device testing guide
- Troubleshooting

### Release Documentation

**RELEASING.md**
- Manual PyPI release steps
- TestPyPI testing workflow
- Version bumping process
- Git tagging conventions

**GITHUB_ACTIONS_SETUP.md**
- GitHub Actions workflow setup
- PyPI API token configuration
- Trusted publishing setup
- Troubleshooting guide
- Security best practices

### Contributing

**CONTRIBUTING.md**
- Development setup
- Contribution workflow
- Coding standards
- Testing guidelines
- Pull request process

**CHANGELOG.md**
- Version history
- Release notes
- Breaking changes

**LEGAL_COMPLIANCE.md**
- Recording laws overview
- Consent requirements
- Best practices

### setup.py
- Dynamic version reading from `__init__.py`
- Long description from README.md
- PyPI classifiers
- Console script entry points:
  - `recordmymeeting` → CLI
  - `recordmymeeting-gui` → GUI

### tests/
- Import tests (no hardware required)
- Device manager logic tests
- Core initialization tests
- All tests pass with `pytest`

## Package Metadata

- **Name**: recordmymeeting
- **Version**: 0.2.0 (dynamically read from `recordmymeeting/__init__.py`)
- **Author**: Sachin Singh <sachincs95@gmail.com>
- **Python**: >=3.8
- **License**: MIT (to be added)
- **Dependencies**: 
  - pyaudio>=0.2.11
  - opencv-python>=4.8.0
  - numpy>=1.19.0
  - mss>=6.1.0

## Console Scripts

After installation via pip:
- `recordmymeeting` - Command-line interface (entry: `recordmymeeting.cli:main`)
- `recordmymeeting-gui` - Graphical interface (entry: `recordmymeeting.gui_app:launch_gui`)

## GitHub Actions Workflow

The `.github/workflows/publish.yml` automates PyPI releases:

1. **Test Stage**: Runs tests on Python 3.8-3.11
2. **Build Stage**: Creates wheel and sdist
3. **Publish Stage**: Uploads to PyPI on GitHub release

**Setup Required**:
- PyPI API token in GitHub secrets (`PYPI_API_TOKEN`)
- See `GITHUB_ACTIONS_SETUP.md` for complete setup

## Release Process

### Automated (Recommended)

1. Bump version in `recordmymeeting/__init__.py`
2. Update `CHANGELOG.md`
3. Commit and push
4. Create GitHub release with tag `vX.Y.Z`
5. GitHub Actions automatically publishes to PyPI

### Manual (Fallback)

1. Follow steps in `RELEASING.md`
2. Use `python -m build` and `python -m twine upload`

## Next Steps

1. ✅ Update author info in `setup.py` (already done: Sachin Singh)
2. ✅ All documentation created and updated
3. ✅ GitHub Actions workflow configured
4. 🔲 Add LICENSE file (MIT recommended)
5. 🔲 Set up GitHub repository
6. 🔲 Configure GitHub Actions secrets
7. 🔲 Create first GitHub release

## Development Workflow

```bash
# Clone and setup
git clone https://github.com/sachincse/recordmymeeting.git
cd recordmymeeting
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1
pip install -e .
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Format code
black recordmymeeting/ tests/

# Build package
python -m build
```
