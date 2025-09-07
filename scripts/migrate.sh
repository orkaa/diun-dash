#!/bin/bash
# Database migration script

set -e

echo "🗄️  Running database migrations..."
uv run alembic -c src/alembic.ini upgrade head
echo "✅ Migrations complete!"