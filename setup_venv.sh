#!/bin/bash

# Exit on error
set -e

# Print commands
set -x

# Remove existing virtual environment if it exists
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

# Create a new virtual environment
echo "Creating new virtual environment..."
python3 -m venv venv

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install required packages
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Verify Pulumi installation
echo "Verifying Pulumi installation..."
python -c "import pulumi; print(f'Pulumi package imported successfully')"

# Verify AWS provider
echo "Verifying AWS provider installation..."
python -c "import pulumi_aws; print(f'Pulumi AWS provider imported successfully')"

echo "Virtual environment setup complete!"
echo "To activate the virtual environment, run: source venv/bin/activate"
