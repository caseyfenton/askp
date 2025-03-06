# ASKP Quickstart

## First-time Setup
```bash
git clone https://github.com/caseyfenton/askp
cd askp
./install.sh --wizard
```

## Common Workflows

### Basic Query
```bash
askp "What is the capital of France?"
```

### Multi-Query Processing
```bash
askp -m "Python best practices" "Python security" "Python performance"
```

### Deep Research Mode
```bash
# Generate a comprehensive research plan
askp -d "Impact of quantum computing on cryptography"
```

### Run Tests
```bash
pytest tests/ -v
```

### Build Documentation
```bash
mkdocs build
```

### Submit PR
1. Create feature branch
2. Add tests
3. Run checks:
```bash
make validate
```
4. Push and create PR

### Update Installation
```bash
askp --update
```
