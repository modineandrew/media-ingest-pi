# Contributing to Media Ingest Pi

Thank you for your interest in contributing to Media Ingest Pi! This document provides guidelines and instructions for contributing.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, use the bug report template and include:

- A clear and descriptive title
- Detailed steps to reproduce the issue
- Expected vs actual behavior
- Your environment (Raspberry Pi model, OS version, Python version)
- Relevant logs and configuration (remove sensitive information)

### Suggesting Features

Feature requests are welcome! Please use the feature request template and include:

- A clear description of the feature
- The use case it solves
- How you envision it working
- Any alternatives you've considered

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following the code style guidelines below
3. **Test your changes** thoroughly on a Raspberry Pi if possible
4. **Update documentation** if you've changed functionality
5. **Write clear commit messages** following conventional commits format
6. **Submit a pull request** with a clear description of your changes

## Development Setup

1. Clone your fork:
```bash
git clone https://github.com/bscholer/media-ingest-pi.git
cd media-ingest-pi
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

3. Copy example configuration:
```bash
cp config/settings.example.yaml config/settings.yaml
cp config/devices.example.yaml config/devices.yaml
```

4. Make your changes and test locally:
```bash
python3 src/main.py
```

## Code Style Guidelines

### Python

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use descriptive variable and function names
- Add docstrings to classes and functions
- Keep functions focused and single-purpose
- Use type hints where appropriate

Example:
```python
def transfer_file(source: Path, destination: Path) -> bool:
    """Transfer a file from source to destination.
    
    Args:
        source: Path to source file.
        destination: Path to destination file.
        
    Returns:
        True if transfer successful, False otherwise.
    """
    # Implementation here
    pass
```

### JavaScript

- Use ES6+ features
- Use meaningful variable names
- Add comments for complex logic
- Keep functions small and focused

### HTML/CSS

- Use semantic HTML
- Follow existing styling patterns
- Keep CSS organized and commented
- Ensure responsive design

## Project Structure

```
media-ingest-pi/
├── src/
│   ├── main.py                 # Main entry point
│   └── media_ingest/
│       ├── core/               # Core business logic
│       ├── mqtt/               # MQTT integration
│       └── web/                # Web interface
├── static/                     # CSS, JavaScript, images
├── templates/                  # HTML templates
├── config/                     # Configuration files
└── tests/                      # Test files (TODO)
```

## Testing

Currently, the project doesn't have automated tests. If you'd like to contribute test coverage, that would be greatly appreciated!

For now, please test your changes manually:

1. Test on actual Raspberry Pi hardware if possible
2. Test with real USB devices and SD cards
3. Test MQTT integration if you've modified that code
4. Test the web interface in multiple browsers
5. Check logs for errors

## Commit Message Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(transfer): add support for exFAT filesystems
fix(device): resolve device detection race condition
docs(readme): update installation instructions
```

## Questions?

If you have questions about contributing, feel free to:

- Open a [Discussion](https://github.com/bscholer/media-ingest-pi/discussions)
- Ask in an issue
- Reach out to the maintainers

## Code of Conduct

Be respectful and inclusive. We're all here to learn and improve the project together.

Thank you for contributing! 🎉

