# ASKP Quickstart

## First-time Setup
```bash
git clone https://github.com/caseyfenton/askp
cd askp
./install.sh --wizard
```

## Common Workflows

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
