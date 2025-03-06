# ASKP Installation Guide

## Quick Install

```bash
# Clone and install manually
git clone https://github.com/caseyfenton/askp.git
cd askp
./install.sh
```

## Installation Options

### Interactive Wizard

For guided installation with configuration:

```bash
./install.sh --wizard
```

The wizard will:
1. Check system requirements
2. Configure installation location
3. Set up API keys
4. Create necessary symlinks
5. Verify the installation

### Custom Installation

```bash
# Install to custom location
./install.sh --prefix=/opt/local

# Install without symlinks
./install.sh --no-symlinks

# Combine options
./install.sh --prefix=/opt/local --no-symlinks
```

## System Requirements

- Python 3.8 or higher
- Write access to installation directory
- Internet connection for dependency installation

## Directory Structure

```
~/.askp/               # User configuration directory
├── env/              # Virtual environment
├── config            # Configuration file
├── .env             # API keys
├── logs/            # Log files
└── backup/          # Backup of previous installations
```

## Command Aliases

The installer creates three commands:
- `askp` - Primary command
- `ask` - Alias for askp
- `askp` - Legacy alias

All commands are functionally identical.

## Environment Management

ASKP manages its own isolated Python environment:
- Located in `~/.askp/env`
- Automatically activated when needed
- Dependencies installed/updated as required

## Configuration

### API Keys

1. Via wizard:
   ```bash
   ./install.sh --wizard
   ```

2. Manual setup:
   ```bash
   echo "PERPLEXITY_API_KEY=your_key_here" > ~/.askp/.env
   ```

### Custom Settings

Edit `~/.askp/config`:
```ini
# ASKP Configuration
version=2.0.0
prefix=/usr/local
```

## Troubleshooting

### Common Issues

1. Command not found
   ```bash
   # Add to PATH if needed
   export PATH="/usr/local/bin:$PATH"
   ```

2. Permission denied
   ```bash
   # Run installer with sudo
   sudo ./install.sh
   ```

3. Python not found
   ```bash
   # Install Python 3
   brew install python3  # macOS
   ```

### Logs

Check installation logs:
```bash
cat ~/.askp/logs/install.log
```

### Clean Install

Remove existing installation:
```bash
rm -rf ~/.askp
rm /usr/local/bin/{askp,ask,askp}
./install.sh --wizard
```

## Development Setup

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run tests:
   ```bash
   pytest tests/
   ```

3. Run linters:
   ```bash
   black src/ tests/
   isort src/ tests/
   pylint src/ tests/
   mypy src/ tests/
   ```

## Security Notes

- API keys are stored in `~/.askp/.env`
- Backups are kept in `~/.askp/backup`
- Virtual environment is isolated
- No system-wide Python changes
