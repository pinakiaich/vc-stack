#!/usr/bin/env python3
"""
Quick diagnostic script to check VC Stack setup
Run this to diagnose why VC Expert Agent isn't working
"""

print("="*60)
print("VC STACK - DIAGNOSTIC CHECK")
print("="*60)
print()

# Check 1: Python version
import sys
print("1. Python Version:")
print(f"   ✅ Python {sys.version.split()[0]}")
print()

# Check 2: Required packages
print("2. Checking Required Packages:")

packages = {
    'streamlit': 'Streamlit (UI framework)',
    'pandas': 'Pandas (data processing)',
    'openpyxl': 'OpenPyXL (Excel support)',
    'openai': 'OpenAI (VC Expert Agent)',
}

missing = []
for package, description in packages.items():
    try:
        __import__(package)
        print(f"   ✅ {package:15} - {description}")
    except ImportError:
        print(f"   ❌ {package:15} - {description} - NOT INSTALLED")
        missing.append(package)

print()

# Check 3: OpenAI setup specifically
print("3. OpenAI Package Check:")
try:
    import openai
    print(f"   ✅ OpenAI version: {openai.__version__}")
    
    # Check if it's the right version
    version_parts = openai.__version__.split('.')
    major = int(version_parts[0])
    if major >= 1:
        print(f"   ✅ Version is compatible (1.0+)")
    else:
        print(f"   ⚠️  Version is old - recommend upgrading to 1.0+")
        print(f"      Run: pip install --upgrade openai")
except ImportError:
    print("   ❌ OpenAI NOT installed")
    print("      This is why VC Expert Agent isn't working!")
    print("      Run: pip install openai")
except Exception as e:
    print(f"   ⚠️  OpenAI check error: {e}")

print()

# Check 4: VC Stack components
print("4. Checking VC Stack Components:")
components = [
    'config.py',
    'vc_expert_agent.py',
    'ai_filter.py',
    'data_processor.py',
    'streamlit_app.py'
]

import os
for component in components:
    if os.path.exists(component):
        print(f"   ✅ {component}")
    else:
        print(f"   ❌ {component} - MISSING")

print()

# Check 5: Try importing VC Expert Agent
print("5. Testing VC Expert Agent Import:")
try:
    from vc_expert_agent import VCExpertAgent
    print("   ✅ VCExpertAgent imported successfully")
    
    # Try to check if it's available
    from config import Config
    config = Config()
    agent = VCExpertAgent(config)
    
    # Check availability (will be False without API key, but import works)
    print(f"   ℹ️  Agent availability check: {agent.is_available()}")
    if not agent.is_available():
        print("      (This is False because no API key is configured - that's OK)")
        print("      The important thing is the import worked!")
    
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    print("      Check if 'openai' package is installed")
except Exception as e:
    print(f"   ⚠️  Error: {e}")

print()

# Summary
print("="*60)
print("SUMMARY")
print("="*60)

if missing:
    print("❌ MISSING PACKAGES:")
    for pkg in missing:
        print(f"   - {pkg}")
    print()
    print("FIX: Run this command:")
    print(f"   pip install {' '.join(missing)}")
    print()
    if 'openai' in missing:
        print("⚠️  OpenAI is missing - this is why VC Expert isn't working!")
else:
    print("✅ All required packages are installed!")
    print()
    print("If VC Expert still isn't working:")
    print("1. Make sure you've entered an API key in the Streamlit app")
    print("2. Check your API key is valid (starts with 'sk-')")
    print("3. Verify you have credits in your OpenAI account")
    print("4. Restart the Streamlit app after installing packages")

print()
print("="*60)
print()
print("To run the app:")
print("   streamlit run streamlit_app.py")
print()

