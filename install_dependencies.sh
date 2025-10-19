#!/bin/bash
# Safe installation script for VC Stack dependencies
# Handles segmentation faults by installing packages one at a time

echo "================================================"
echo "VC Stack - Safe Dependency Installation"
echo "================================================"
echo ""

# Change to vc-stack directory
cd "$(dirname "$0")"

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet

echo ""
echo "Installing packages one at a time (to avoid segfaults)..."
echo ""

packages=(
    "wheel"
    "setuptools"
    "numpy"
    "pandas"
    "openpyxl"
    "openai"
    "python-dotenv"
    "streamlit"
)

failed_packages=()

for package in "${packages[@]}"; do
    echo -n "Installing $package... "
    if pip install --no-cache-dir "$package" > /dev/null 2>&1; then
        echo "✅"
    else
        echo "❌ FAILED"
        failed_packages+=("$package")
    fi
done

echo ""
echo "================================================"
echo "Installation Summary"
echo "================================================"

if [ ${#failed_packages[@]} -eq 0 ]; then
    echo "✅ All packages installed successfully!"
    echo ""
    echo "To run the app:"
    echo "  source venv/bin/activate"
    echo "  streamlit run streamlit_app.py"
else
    echo "❌ Some packages failed to install:"
    for pkg in "${failed_packages[@]}"; do
        echo "  - $pkg"
    done
    echo ""
    echo "Try installing failed packages manually:"
    for pkg in "${failed_packages[@]}"; do
        echo "  pip install $pkg"
    done
fi

echo ""
echo "================================================"

