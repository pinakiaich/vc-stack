#!/usr/bin/env python3
"""
Simple test to verify OpenAI API key and credits
"""

print("="*60)
print("OpenAI API Test")
print("="*60)

# Get API key
api_key = input("\nEnter your OpenAI API key: ").strip()

if not api_key:
    print("❌ No API key provided")
    exit(1)

if not api_key.startswith('sk-'):
    print("⚠️  Warning: API key doesn't start with 'sk-' - might be invalid")

print(f"\n✅ API Key: {api_key[:10]}...{api_key[-4:]}")

# Test import
print("\n1. Importing OpenAI...")
try:
    import openai
    print(f"   ✅ OpenAI version: {openai.__version__}")
    
    version = int(openai.__version__.split('.')[0])
    print(f"   ℹ️  API version: {'1.0+ (new)' if version >= 1 else '0.x (old)'}")
except ImportError:
    print("   ❌ OpenAI not installed")
    print("   Run: pip install openai")
    exit(1)

# Test simple API call
print("\n2. Testing API call...")
try:
    if version >= 1:
        # New API
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        print("   Making test request...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Reply with just 'API test successful'"}
            ],
            max_tokens=20
        )
        
        result = response.choices[0].message.content
        print(f"   ✅ Response: {result}")
        
    else:
        # Old API
        openai.api_key = api_key
        
        print("   Making test request...")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Reply with just 'API test successful'"}
            ],
            max_tokens=20
        )
        
        result = response.choices[0].message.content
        print(f"   ✅ Response: {result}")
    
    print("\n" + "="*60)
    print("✅ SUCCESS! Your OpenAI API is working perfectly!")
    print("="*60)
    print("\nYour API key and credits are valid.")
    print("The VC Expert Agent should work with this key.")
    print("\nNext steps:")
    print("1. Copy this API key")
    print("2. Enter it in the Streamlit app")
    print("3. Try filtering again")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ API call FAILED!")
    print(f"\nError Type: {type(e).__name__}")
    print(f"Error Message: {str(e)}")
    
    print("\n" + "="*60)
    print("DIAGNOSIS:")
    print("="*60)
    
    error_str = str(e).lower()
    
    if 'quota' in error_str or '429' in str(e):
        print("\n❌ QUOTA EXCEEDED - No credits available")
        print("\nSolutions:")
        print("1. Check your balance: https://platform.openai.com/account/billing/overview")
        print("2. Add credits: https://platform.openai.com/account/billing/payment-methods")
        print("3. Add at least $10 to get started")
        print("\nNote: Free tier credits ($5) expire after 3 months")
        
    elif 'rate' in error_str and 'limit' in error_str:
        print("\n⚠️  RATE LIMIT - Too many requests")
        print("\nSolutions:")
        print("1. Wait 1-2 minutes and try again")
        print("2. Upgrade your OpenAI plan for higher limits")
        
    elif '401' in str(e) or 'unauthorized' in error_str or 'authentication' in error_str:
        print("\n❌ INVALID API KEY")
        print("\nSolutions:")
        print("1. Generate new key: https://platform.openai.com/api-keys")
        print("2. Make sure you copied the entire key")
        print("3. Check key hasn't been revoked")
        
    elif '404' in str(e) or 'not found' in error_str:
        print("\n❌ MODEL NOT FOUND")
        print("\nYour account doesn't have access to gpt-3.5-turbo")
        print("\nSolutions:")
        print("1. Check your account tier")
        print("2. Try gpt-4 if you have access")
        
    elif 'network' in error_str or 'connection' in error_str:
        print("\n❌ NETWORK ERROR")
        print("\nCheck your internet connection")
        
    else:
        print("\n❓ UNKNOWN ERROR")
        print("\nFull error details above.")
        print("Copy this error and search OpenAI docs or contact support.")
    
    print("\n" + "="*60)
    print("\nCheck OpenAI status: https://status.openai.com")
    print("View your usage: https://platform.openai.com/usage")
    print("="*60)

