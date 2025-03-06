# ASKP Development Guide

## Development Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/caseyfenton/askp.git
   cd askp
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Project Structure

```

├── docs/                  # Documentation
├── scripts/              # Command wrappers
├── src/                  # Source code
│   └── askp/
│       ├── cli.py        # CLI interface
│       ├── cost_tracking.py  # Cost analysis
│       └── wizard/       # Installation wizard
├── tests/                # Test suite
├── install.sh            # Installer script
├── setup.py             # Package setup
└── requirements.txt      # Dependencies
```

## Development Workflow

### 1. Code Style

We follow PEP 8 with some modifications:
- Line length: 88 characters (Black default)
- Quotes: Double quotes for docstrings, single for strings
- Import order: isort with black compatibility

### 2. Testing

Run tests:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_cost_tracking.py

# Run tests matching pattern
pytest -k "test_format"
```

### 3. Type Checking

```bash
# Check types with mypy
mypy src/ tests/

# Generate stub files
stubgen -p askp
```

### 4. Linting

```bash
# Run all linters
make lint

# Or individually:
black src/ tests/
isort src/ tests/
pylint src/ tests/
flake8 src/ tests/
```

### 5. Documentation

- Use Google-style docstrings
- Keep README.md up to date
- Document all public APIs
- Include examples in docstrings

Example:
```python
def format_cost(cost: float) -> str:
    """Format cost with appropriate decimal places.
    
    Args:
        cost: The cost value to format
        
    Returns:
        Formatted cost string with $ prefix
        
    Example:
        >>> format_cost(1.23456)
        '$1.23'
    """
```

### 6. Git Workflow

1. Create feature branch:
   ```bash
   git checkout -b feature/cost-analysis
   ```

2. Make changes and commit:
   ```bash
   git add .
   git commit -m "feat: add cost analysis feature"
   ```

3. Push and create PR:
   ```bash
   git push origin feature/cost-analysis
   ```

### 7. Release Process

1. Update version:
   - setup.py
   - scripts/askp
   - docs/

2. Create changelog entry

3. Tag release:
   ```bash
   git tag -a v2.0.0 -m "Release v2.0.0"
   git push origin v2.0.0
   ```

## Debugging Tips

### 1. Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. Use Rich for Development

```python
from rich import print, inspect
inspect(my_object)
```

### 3. Test Installation

```bash
# Test in temporary directory
INSTALL_TEST_DIR=$(mktemp -d)
./install.sh --prefix="$INSTALL_TEST_DIR"
```

### 4. Profile Code

```python
import cProfile
cProfile.run('my_function()')
```

## Common Issues

### 1. Installation Problems

Check:
- Python version
- Permissions
- Virtual environment
- PATH settings

### 2. API Issues

Verify:
- API key in ~/.askp/.env
- Network connectivity
- Rate limits

### 3. Cost Tracking

Debug:
- Log file permissions
- JSON format
- File paths

## Contributing

1. Fork repository
2. Create feature branch
3. Add tests
4. Update documentation
5. Submit PR

## Security

- Never commit API keys
- Use .env for secrets
- Validate all inputs
- Check file permissions
- Sanitize paths
