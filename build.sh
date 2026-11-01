#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "==> Upgrading pip..."
pip install --upgrade pip

echo "==> Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "==> Running database migrations with Alembic..."
alembic upgrade head

echo "==> Build process completed successfully!"
