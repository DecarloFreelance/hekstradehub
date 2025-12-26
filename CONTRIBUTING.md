# Contributing to HekTradeHub

## Before You Commit

1. **Never commit sensitive data:**
   - `.env` file (contains API keys)
   - `trade_journal.json` (personal trading data)
   - Log files
   - Archive folder

2. **Test your changes:**
   ```bash
   ./status  # Verify system still works
   python -m pytest tests/  # Run tests (if available)
   ```

3. **Follow the structure:**
   - Trading scripts → `trading/`
   - Analysis tools → `analysis/`
   - Automation → `automation/`
   - Utilities → `utils/`

## Git Workflow

```bash
# Check what's being committed
git status

# Add files (gitignore will protect sensitive data)
git add .

# Commit with clear message
git commit -m "feat: add new feature"

# Push to remote
git push origin main
```

## Pre-commit Hook

A pre-commit hook is installed to prevent accidentally committing:
- `.env` files
- API credentials
- Sensitive data

## Code Style

- Follow PEP 8 for Python
- Add docstrings to functions
- Keep functions modular
- Handle errors gracefully

## Questions?

Open an issue or discussion on GitHub.
