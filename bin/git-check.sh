#!/bin/bash
# Git Push Checklist
# Run this before pushing to verify everything is safe

echo "🔍 GIT PUSH READINESS CHECK"
echo "======================================"
echo ""

# Check 1: Sensitive files
echo "✓ Checking sensitive files are protected..."
if git check-ignore .env > /dev/null 2>&1; then
    echo "  ✓ .env is gitignored"
else
    echo "  ✗ WARNING: .env is NOT gitignored!"
    exit 1
fi

if git check-ignore .venv > /dev/null 2>&1; then
    echo "  ✓ .venv is gitignored"
else
    echo "  ✗ WARNING: .venv is NOT gitignored!"
    exit 1
fi

if git check-ignore logs/ > /dev/null 2>&1; then
    echo "  ✓ logs/ is gitignored"
fi

if git check-ignore archive/ > /dev/null 2>&1; then
    echo "  ✓ archive/ is gitignored"
fi

echo ""

# Check 2: No API keys in staged files
echo "✓ Scanning for API keys in staged files..."
if git diff --cached | grep -qE 'KUCOIN_API_(KEY|SECRET|PASSPHRASE).*=.*[^_here]'; then
    echo "  ✗ WARNING: Possible API keys detected!"
    echo "  Please review your staged changes."
    exit 1
else
    echo "  ✓ No API keys detected in staged files"
fi

echo ""

# Check 3: Show what will be committed
echo "📋 Files ready to commit:"
git status --short | grep -E "^[AM]" | wc -l
echo ""

# Check 4: Show protected files
echo "🔒 Protected files (NOT in repo):"
git status --ignored --short | grep "^!!" | head -5
echo ""

# Check 5: Git status
echo "📊 Git Status:"
git status --short --branch
echo ""

# Summary
echo "======================================"
echo "✅ Repository is ready for git push!"
echo ""
echo "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Commit: git commit -m 'feat: major repo restructure'"
echo "  3. Push: git push origin main"
echo ""
