# Contributing to RecordMyMeeting

Thank you for considering contributing to RecordMyMeeting! This document outlines the process and standards.

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/sachincse/recordmymeeting.git
   cd recordmymeeting
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
   ```

3. **Install development dependencies**
   ```bash
   pip install -e .
   pip install -r requirements-dev.txt
   ```

4. **Run tests**
   ```bash
   pytest tests/ -v
   ```

## How to Contribute

1. **Fork the repository** on GitHub
2. **Create a feature branch** from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** with clear, focused commits
4. **Write tests** for new features or bug fixes
5. **Run the test suite** to ensure nothing breaks
   ```bash
   pytest tests/ -v
   ```
6. **Format your code** (optional but recommended)
   ```bash
   black recordmymeeting/ tests/
   ```
7. **Submit a pull request** with a clear description

## Coding Standards

- **Code Style**: Follow PEP 8; use `black` for formatting
- **Documentation**: Write docstrings for all public functions and classes
- **Testing**: Add tests for all new code; maintain test coverage
- **Commits**: Use clear, descriptive commit messages
- **Type Hints**: Use type hints where appropriate

## Testing Guidelines

- Tests should not require audio hardware to run
- Use mocks/fixtures for hardware-dependent functionality
- Aim for high test coverage on core logic
- Run `pytest tests/ -v` before submitting PR

## Pull Request Process

1. Update CHANGELOG.md with your changes
2. Ensure all tests pass
3. Update documentation if needed
4. Request review from maintainers
5. Address any feedback

## Reporting Issues

- Use GitHub Issues to report bugs
- Provide clear reproduction steps
- Include system information (OS, Python version)
- Check existing issues before creating new ones

## Questions?

Feel free to open an issue for questions or discussions!
