#!/bin/bash
# Development setup script for LinkNower

set -e

echo "🚀 Setting up LinkNower development environment..."

# Find Python 3.10+
if command -v python3.10 &> /dev/null; then
    PYTHON_CMD=python3.10
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD=python3.12
elif command -v python3 &> /dev/null && python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
    PYTHON_CMD=python3
else
    echo "❌ Python 3.10+ not found"
    echo "Please install Python 3.10 or higher:"
    echo "  brew install python@3.10"
    exit 1
fi

python_version=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install package in editable mode with dev dependencies
echo "Installing LinkNower and dependencies..."
pip install -e ".[dev]"

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the environment:"
echo "  source venv/bin/activate"
echo ""
echo "To run tests:"
echo "  pytest"
echo ""
echo "To try the CLI:"
echo "  lk --help"
