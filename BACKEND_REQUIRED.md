# ⚠️ Backend Required - Quick Start Guide

## The Error You're Seeing

```
❌ Could not connect to API: HTTPConnectionPool(host='localhost', port=8000): 
Connection refused
```

This means the **FastAPI backend is not running**. The Deal Workspace features require it.

## Quick Fix: Start the Backend

### Step 1: Open a New Terminal

Open a **separate terminal window** (keep your Streamlit terminal running).

### Step 2: Start the Backend

Run this command:

```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack/backend"
uvicorn app.main:app --reload --port 8000
```

### Step 3: Verify It's Running

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### Step 4: Test the Connection

In a new terminal or browser:
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"ok"}`

Or visit: http://localhost:8000/health

### Step 5: Refresh Streamlit

Go back to your Streamlit app and refresh the page. The error should be gone!

## Running Both Servers

You need **TWO terminals** running simultaneously:

**Terminal 1 (Backend):**
```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack/backend"
uvicorn app.main:app --reload --port 8000
```
✅ Keep this running - don't close it!

**Terminal 2 (Frontend/Streamlit):**
```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
streamlit run streamlit_app.py
```

## What Happens Now

Once the backend is running:

1. ✅ Filter companies → Top 10 will **auto-create as deals**
2. ✅ Deals appear in the sidebar dropdown
3. ✅ You can select deals and conduct research
4. ✅ All data is saved to the database

## Troubleshooting

### "Port 8000 already in use"
Use a different port:
```bash
uvicorn app.main:app --reload --port 8001
```

### "Database not found"
Initialize it first:
```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
python backend/app/init_db.py
```

### "Module not found" errors
Install dependencies:
```bash
pip install -r requirements.txt
```

## Need More Help?

See:
- `START_BACKEND.md` - Detailed backend setup
- `TROUBLESHOOT_BACKEND.md` - Common issues and solutions
- `QUICK_START_STEP3.md` - Step-by-step guide
