#!/bin/bash
# ASKP PyPI Deployment Script
# Created by Casey Fenton

set -e  # Exit on error

echo "🚀 Preparing ASKP for PyPI deployment..."

# Clean up previous builds
echo "🧹 Cleaning up previous builds..."
rm -rf build/ dist/ *.egg-info/

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install build dependencies
echo "📦 Installing build dependencies..."
pip install --upgrade pip setuptools wheel build twine

# Build the package
echo "🏗️ Building the package..."
python -m build

# Check the package
echo "🔍 Checking the package with twine..."
twine check dist/*

# Ask for confirmation before uploading to PyPI
echo ""
echo "📝 Package details:"
echo "   Name: askp"
echo "   Version: $(grep -m 1 "version" pyproject.toml | cut -d '"' -f 2)"
echo "   Author: Casey Fenton"
echo ""
read -p "🚀 Upload to PyPI? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📤 Uploading to PyPI..."
    twine upload dist/*
    echo "✅ Package uploaded successfully!"
else
    echo "⏸️ Upload cancelled."
    echo "📦 Distribution files are available in the dist/ directory."
fi

# Deactivate virtual environment
echo "🔌 Deactivating virtual environment..."
deactivate

echo "✨ Done!"
