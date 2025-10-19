#!/usr/bin/env python3
"""
Test script to diagnose VC Expert Agent issues
"""
import sys
print("Testing VC Expert Agent...")
print("="*60)

# Test 1: Import check
print("\n1. Testing imports...")
try:
    import openai
    print(f"   ✅ OpenAI imported (version {openai.__version__})")
except ImportError as e:
    print(f"   ❌ OpenAI import failed: {e}")
    sys.exit(1)

# Test 2: VC Expert Agent import
print("\n2. Testing VC Expert Agent import...")
try:
    from vc_expert_agent import VCExpertAgent
    from config import Config
    print("   ✅ VC Expert Agent imported")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 3: Initialize with mock config
print("\n3. Testing initialization...")
class MockConfig:
    def get_openai_key(self):
        # You need to put your REAL API key here for testing
        key = input("   Enter your OpenAI API key (or press Enter to skip): ").strip()
        return key if key else None
    
    def get_ai_model(self):
        return "gpt-3.5-turbo"

config = MockConfig()
agent = VCExpertAgent(config)
print("   ✅ Agent initialized")

api_key = config.get_openai_key()
if not api_key:
    print("\n❌ No API key provided - cannot test API calls")
    print("   Rerun with your API key to test full functionality")
    sys.exit(0)

print(f"   ℹ️  API key: {api_key[:10]}...")
print(f"   ℹ️  Agent available: {agent.is_available()}")

# Test 4: Simple API call
print("\n4. Testing OpenAI API call...")
try:
    # Detect OpenAI version
    version = int(openai.__version__.split('.')[0])
    
    if version >= 1:
        # New API (1.0+)
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'test successful'"}],
            max_tokens=10
        )
        print(f"   ✅ API call successful: {response.choices[0].message.content}")
    else:
        # Old API (0.x)
        openai.api_key = api_key
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'test successful'"}],
            max_tokens=10
        )
        print(f"   ✅ API call successful: {response.choices[0].message.content}")
except Exception as e:
    print(f"   ❌ API call failed: {type(e).__name__}: {e}")
    print("\n   This is why VC Expert isn't working!")
    sys.exit(1)

# Test 5: Test with sample data
print("\n5. Testing VC Expert with sample data...")
sample_firms = [
    {
        'name': 'Test AI Company',
        'description': 'B2B artificial intelligence platform for enterprises',
        'industry': 'AI/ML',
        'stage': 'Series B',
        'revenue': '$10M ARR',
        'location': 'San Francisco'
    }
]

criteria = "B2B AI companies with over $5M revenue"

try:
    results = agent.analyze_firms(sample_firms, criteria, top_n=1)
    print(f"   ✅ Analysis successful!")
    print(f"\n   Results:")
    for result in results:
        print(f"   - {result['name']}: {result['score']}/100")
        print(f"     Reason: {result['reason'][:100]}...")
except Exception as e:
    print(f"   ❌ Analysis failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("✅ ALL TESTS PASSED!")
print("VC Expert Agent is working correctly.")
print("\nIf it's not working in Streamlit:")
print("1. Make sure you entered the SAME API key in the Streamlit app")
print("2. Check the terminal running Streamlit for error messages")
print("3. Restart the Streamlit app")
print("="*60)

