#!/bin/bash
# Flamboyance Demo Pre-Flight Checklist
# Run this before demos to verify everything is set up correctly.

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🦩 Flamboyance Demo Pre-Flight Checklist"
echo "========================================="
echo ""

ERRORS=0

# 1. Check Python
echo -n "1. Python 3.10+... "
if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$(echo $PY_VERSION | cut -d. -f1)
    PY_MINOR=$(echo $PY_VERSION | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ]; then
        echo -e "${GREEN}✓${NC} Python $PY_VERSION"
    else
        echo -e "${RED}✗${NC} Python $PY_VERSION (need 3.10+)"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}✗${NC} python3 not found"
    ERRORS=$((ERRORS + 1))
fi

# 2. Check package installation
echo -n "2. Flamboyance package... "
if python3 -c "import agents" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} installed"
else
    echo -e "${RED}✗${NC} not installed (run: pip install -e .)"
    ERRORS=$((ERRORS + 1))
fi

# 3. Check Playwright
echo -n "3. Playwright... "
if python3 -c "import playwright" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} installed"
else
    echo -e "${RED}✗${NC} not installed (run: pip install playwright)"
    ERRORS=$((ERRORS + 1))
fi

# 4. Check Chromium browser
echo -n "4. Chromium browser... "
# Try to find chromium in playwright's browser path
if python3 -c "
from playwright._impl._driver import compute_driver_executable
import os
import glob

driver_dir = os.path.dirname(compute_driver_executable())
# Look for chromium in the playwright cache
cache_dir = os.path.expanduser('~/Library/Caches/ms-playwright')
if not os.path.exists(cache_dir):
    cache_dir = os.path.expanduser('~/.cache/ms-playwright')
chromium_dirs = glob.glob(os.path.join(cache_dir, 'chromium-*'))
if chromium_dirs:
    exit(0)
exit(1)
" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} installed"
else
    echo -e "${YELLOW}!${NC} may need install (run: playwright install chromium)"
    # Don't count as error - it might still work
fi

# 5. Check MCP package
echo -n "5. MCP package... "
if python3 -c "import mcp" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} installed"
else
    echo -e "${RED}✗${NC} not installed (run: pip install 'mcp[cli]')"
    ERRORS=$((ERRORS + 1))
fi

# 6. Check MCP server can start
echo -n "6. MCP server module... "
if python3 -c "from flamboyance_mcp.server import mcp" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} loadable"
else
    echo -e "${RED}✗${NC} failed to load"
    ERRORS=$((ERRORS + 1))
fi

# 7. Check for LLM API key (optional)
echo -n "7. LLM API key (optional)... "
if [ -n "$GROQ_API_KEY" ]; then
    echo -e "${GREEN}✓${NC} GROQ_API_KEY set"
elif [ -n "$OPENAI_API_KEY" ]; then
    echo -e "${GREEN}✓${NC} OPENAI_API_KEY set"
else
    echo -e "${YELLOW}○${NC} not set (LLM mode will fail, heuristic mode OK)"
fi

# 8. Quick import test
echo -n "8. Core imports... "
if python3 -c "
from agents.agent import run_agent
from agents.runner_local import run_local
from agents.persona import DEFAULT_PERSONAS
from agents.report import generate_report
" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} all modules load"
else
    echo -e "${RED}✗${NC} import errors"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "========================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready for demo.${NC}"
    echo ""
    echo "Quick test commands:"
    echo "  # Heuristic mode (no API key needed):"
    echo "  python -m agents.runner_local --url http://localhost:3000 --batch-size 2"
    echo ""
    echo "  # LLM mode (requires GROQ_API_KEY):"
    echo "  python -m agents.runner_local --url http://localhost:3000 --llm --batch-size 2"
    exit 0
else
    echo -e "${RED}✗ $ERRORS check(s) failed. Fix issues above before demo.${NC}"
    exit 1
fi
