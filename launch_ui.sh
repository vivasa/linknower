#!/bin/bash
# Launch LinkNower Streamlit UI

set -e

echo "🚀 Launching LinkNower UI..."

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "venv" ]; then
        echo "Activating virtual environment..."
        source venv/bin/activate
    else
        echo "⚠️  No virtual environment found. Run ./setup.sh first."
        exit 1
    fi
fi

# Launch Streamlit
echo "Opening browser at http://localhost:8501"
streamlit run src/linknower/ui/app.py
