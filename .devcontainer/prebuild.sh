#!/bin/bash
set -e

echo "Starting pre-build process..."

# Create necessary directories
mkdir -p /workspaces/testus-patronus/backend/data/db
mkdir -p /workspaces/testus-patronus/backend/data/uploads

# Install Python dependencies
cd /workspaces/testus-patronus/backend
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Install development tools
pip install pytest pytest-cov black flake8 mypy isort pylint

# Install frontend dependencies
cd /workspaces/testus-patronus/frontend
npm install

echo "Pre-build process completed successfully!" 