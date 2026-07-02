#!/bin/bash

# Tool Selection Testing Script
# Run DeepEval tests for LLM tool selection validation

set -e

echo "==================================="
echo "Tool Selection Testing with DeepEval"
echo "==================================="
echo ""

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY not set"
    echo ""
    echo "Please set your API key:"
    echo "  export ANTHROPIC_API_KEY='your-api-key-here'"
    echo ""
    exit 1
fi

echo "API Key: Found ✓"
echo ""

# Install dependencies if needed
echo "Installing dependencies..."
uv sync --extra ai --quiet
echo "Dependencies: Ready ✓"
echo ""

# Run tests
echo "Running tool selection tests..."
echo "-----------------------------------"
uv run pytest tests/test_tool_selection.py -v "$@"

echo ""
echo "==================================="
echo "Tests Complete!"
echo "==================================="
