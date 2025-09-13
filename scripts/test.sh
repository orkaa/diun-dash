#!/bin/bash
# Test script for diun-dash
# Runs the complete test suite

set -e

echo "🧪 Running test suite..."

# Run tests with verbose output
uv run pytest -v

echo "✅ Test suite completed"