#!/bin/bash
# Development server script

set -e

echo "🚀 Starting development server with uv..."
uv run uvicorn src.main:app --host 0.0.0.0 --port 8554 --reload --log-level info --access-log