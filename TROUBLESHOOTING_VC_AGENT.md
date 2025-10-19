# 🔧 Troubleshooting: VC Expert Agent Not Working

## Issue: Still Seeing Generic Reasoning

If you're seeing:
```
Reason: Description mentions 'artificial', 'intelligence'
```

Instead of:
```
Reason: Strong B2B AI play with $10M ARR (2x the $5M threshold)...
```

**This means the VC Expert Agent isn't running** - it's falling back to keyword matching.

---

## 🔍 Common Causes & Solutions

### 1. No API Key Entered ⚠️

**Problem:** You haven't entered your OpenAI API key in the app

**Check:**
- Look at the top of the Streamlit app
- Do you see: "⚠️ OpenAI API Key Required"?

**Solution:**
1. Get an API key from https://platform.openai.com/api-keys
2. Enter it in the "🔑 Enter your OpenAI API Key" field
3. Click "Save API Key"
4. You should see: "✅ OpenAI API Key configured"
5. Try filtering again

---

### 2. OpenAI Package Not Installed 📦

**Problem:** The `openai` Python package isn't installed

**Check:**
Run this in your terminal:
```bash
python3 -c "import openai; print('✅ OpenAI installed')"
```

If you see an error, OpenAI isn't installed.

**Solution:**
```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
pip install openai
```

Or install all requirements:
```bash
pip install -r requirements_colab.txt
```

---

### 3. Wrong OpenAI API Version 🔄

**Problem:** You have an incompatible OpenAI package version

**Check:**
```bash
pip show openai
```

**Solution:**
Update to the correct version:
```bash
pip install "openai>=1.0.0"
```

---

### 4. API Key Invalid or No Credits 💳

**Problem:** Your API key doesn't work or has no credits

**Check:**
- Does your API key start with `sk-`?
- Do you have credits in your OpenAI account?

**Solution:**
1. Log into https://platform.openai.com
2. Check your API key is active
3. Check your billing/credits
4. Generate a new key if needed
5. Re-enter in the app

---

## 🎯 Quick Diagnostic Steps

### Step 1: Check If App Is Using VC Expert

**Look for these messages when filtering:**

✅ **Working:**
```
🎯 Using VC Expert Agent - Professional investment analysis
✨ VC Expert Analysis Complete
```

❌ **Not Working:**
```
ℹ️ Using basic keyword matching (no API key)
```
or
```
⚠️ No API key configured - Using basic keyword matching fallback
```

---

### Step 2: Check Console/Terminal Output

Run the app from terminal to see logs:
```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
streamlit run streamlit_app.py
```

**Look for:**

✅ **Working:**
```
INFO - Using VC Expert Agent for analysis
INFO - VC Expert analysis complete - 10 results
```

❌ **Not Working:**
```
WARNING - VC Expert Agent not available - using fallback
```
or
```
ERROR - VC Expert Agent missing dependency: No module named 'openai'
```
or
```
ERROR - VC Expert Agent configuration issue: OpenAI API key not configured
```

---

### Step 3: Test OpenAI Connection

Create a test file `test_openai.py`:
```python
import openai
import os

# Test 1: Check import
print("✅ OpenAI module imported")

# Test 2: Check API key
api_key = input("Enter your OpenAI API key: ")
openai.api_key = api_key

# Test 3: Make a simple API call
try:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'test successful'"}],
        max_tokens=10
    )
    print("✅ API call successful:", response.choices[0].message.content)
except Exception as e:
    print(f"❌ API call failed: {e}")
```

Run it:
```bash
python test_openai.py
```

---

## 🛠️ Fix Based on Error Message

### Error: "VC Expert Agent not available - using fallback"

**Cause:** No API key OR OpenAI not installed

**Fix:**
1. Install OpenAI: `pip install openai`
2. Enter API key in the app
3. Restart the app

---

### Error: "OpenAI module not installed"

**Cause:** OpenAI package missing

**Fix:**
```bash
pip install openai
```

Then restart the Streamlit app.

---

### Error: "OpenAI API key not configured"

**Cause:** No API key entered in the app

**Fix:**
1. Get key from https://platform.openai.com/api-keys
2. Enter at top of app
3. Click "Save API Key"
4. Should see "✅ OpenAI API Key configured"

---

### Error: "Rate limit" or "Quota exceeded"

**Cause:** You've hit OpenAI's usage limits or have no credits

**Fix:**
1. Wait a few minutes (rate limit)
2. Add credits to your OpenAI account (quota)
3. Check your usage at https://platform.openai.com/usage

---

### Error: "Invalid API key"

**Cause:** Wrong key or key revoked

**Fix:**
1. Verify key starts with `sk-`
2. Generate new key at https://platform.openai.com/api-keys
3. Enter new key in app

---

## ✅ Verification Checklist

Run through this checklist:

- [ ] OpenAI package installed: `pip list | grep openai`
- [ ] API key obtained from OpenAI platform
- [ ] API key entered in the Streamlit app
- [ ] "✅ OpenAI API Key configured" message shows
- [ ] App shows "🎯 Using VC Expert Agent" when filtering
- [ ] Results show detailed reasoning (not just "Description mentions...")
- [ ] No error messages in console/terminal

---

## 🚀 Complete Setup from Scratch

If nothing works, start fresh:

### Step 1: Install Dependencies
```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
pip install streamlit pandas openpyxl openai python-dotenv numpy
```

### Step 2: Get API Key
1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-`)

### Step 3: Run App
```bash
streamlit run streamlit_app.py
```

### Step 4: Configure in UI
1. App opens in browser
2. See "⚠️ OpenAI API Key Required"
3. Paste your key in the field
4. Click "Save API Key"
5. See "✅ OpenAI API Key configured"

### Step 5: Test
1. Upload Excel file
2. Enter criteria
3. Click "Filter Top 10 Firms"
4. Should see "🎯 Using VC Expert Agent"
5. Results should have detailed reasoning

---

## 📊 What You Should See

### Top of App (Before Upload)

❌ **Wrong:**
```
⚠️ OpenAI API Key Required - Please enter your API key below
[Empty text field]
```

✅ **Right:**
```
✅ OpenAI API Key configured
[🔄 Change API Key]
```

### During Filtering

❌ **Wrong:**
```
ℹ️ Using basic keyword matching (no API key)
[Spinner: "Matching keywords..."]
```

✅ **Right:**
```
🎯 Using VC Expert Agent - Professional investment analysis
[Spinner: "VC Expert analyzing firms..."]
```

### After Filtering

❌ **Wrong:**
```
💡 Tip: Add an OpenAI API key above for VC Expert analysis

Results:
1. Company Name
   Reason: Description mentions 'artificial', 'intelligence'
```

✅ **Right:**
```
✨ VC Expert Analysis Complete - Results analyzed by AI with VC expertise

Results:
1. Company Name
   Reason: Strong B2B AI play with $10M ARR (2x the $5M threshold)...
```

---

## 🆘 Still Not Working?

If you've tried everything:

1. **Check the console** where you ran `streamlit run` for error messages
2. **Try the test script** above to verify OpenAI works
3. **Restart the Streamlit app** completely
4. **Check your OpenAI account** has credits
5. **Try a fresh API key** in case the old one was revoked

---

## 💡 Quick Test

Want to quickly verify VC Expert works?

```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
python3 -c "
from config import Config
from vc_expert_agent import VCExpertAgent
import streamlit as st

# Simulate session state
class MockState:
    def get(self, key): return 'sk-test' if key == 'openai_key' else None
st.session_state = MockState()

config = Config()
agent = VCExpertAgent(config)
print('VC Expert available:', agent.is_available())
"
```

Should print: `VC Expert available: True`

---

**Summary:** The most common issue is either no API key entered or OpenAI package not installed. Follow the steps above to fix it! 🚀

