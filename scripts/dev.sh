#!/bin/bash
# Development server script

set -e

# Set development webhook token if not already set
export DIUN_WEBHOOK_TOKEN=${DIUN_WEBHOOK_TOKEN:-"dev-webhook-token"}

echo "🚀 Starting development server with uv..."
echo "📡 Using webhook token: $DIUN_WEBHOOK_TOKEN"
uv run uvicorn src.main:app --host 0.0.0.0 --port 8554 --reload --log-level info --access-log