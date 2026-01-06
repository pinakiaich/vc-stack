# 🚀 How to Run the Application

## Prerequisites

Make sure you have all dependencies installed:
```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
pip install -r requirements.txt
```

## Step 1: Initialize Database (First Time Only)

If you haven't initialized the database yet:
```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
python backend/app/init_db.py
```

## Step 2: Start Backend (Terminal 1)

Open your first terminal and run:

```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack/backend"
uvicorn app.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**✅ Keep this terminal running!** Don't close it.

## Step 3: Verify Backend is Running

In a **new terminal** (or browser), test the health endpoint:

```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{"status":"ok"}
```

Or visit in your browser: **http://localhost:8000/health**

You should see: `{"status":"ok"}`

## Step 4: Start Streamlit (Terminal 2)

Open a **second terminal** (keep Terminal 1 running!) and run:

```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
streamlit run streamlit_app.py
```

**Expected output:**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

**✅ Keep this terminal running too!**

## Step 5: Open the Application

Your browser should automatically open to: **http://localhost:8501**

If not, manually open: **http://localhost:8501**

## Quick Reference Commands

### Terminal 1 (Backend):
```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack/backend"
uvicorn app.main:app --reload --port 8000
```

### Terminal 2 (Frontend):
```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
streamlit run streamlit_app.py
```

### Health Check:
```bash
curl http://localhost:8000/health
```

## What to Test

1. **Upload Excel file** with company data
2. **Enter heuristics** (e.g., "AI startups with revenue >$1M")
3. **Click "Filter Top 10 Firms"** → Should see results table
4. **Click a company name** → Table should stay visible, sidebar form should auto-fill
5. **Create Deal** → Should save to backend
6. **Select Deal** from sidebar dropdown
7. **Conduct Research** → Should run company research

## Troubleshooting

### ❌ "Connection refused" Error

**Problem:** Backend is not running

**Solution:** 
1. Go to Terminal 1
2. Make sure backend is running (see Step 2)
3. Check for errors in Terminal 1

### ❌ Port 8000 Already in Use

**Problem:** Another process is using port 8000

**Solution 1:** Find and kill the process
```bash
lsof -ti:8000 | xargs kill -9
```

**Solution 2:** Use a different port
```bash
# In Terminal 1, use port 8001
uvicorn app.main:app --reload --port 8001
```

Then update `streamlit_app.py` (around line 75):
```python
API_BASE_URL = "http://localhost:8001"  # Change from 8000 to 8001
```

### ❌ Database Error

**Problem:** Database not initialized

**Solution:**
```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
python backend/app/init_db.py
```

### ❌ Module Not Found

**Problem:** Dependencies not installed

**Solution:**
```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
pip install -r requirements.txt
```

### ❌ Streamlit Not Found

**Problem:** Streamlit not installed

**Solution:**
```bash
pip install streamlit
```

## Stopping the Application

1. **Stop Backend:** In Terminal 1, press `Ctrl+C`
2. **Stop Streamlit:** In Terminal 2, press `Ctrl+C`

## Next Steps After Testing

Once everything works:
1. Test the full workflow (filter → select → research)
2. Verify table persistence (click company names)
3. Check auto-fill functionality
4. Test research quality

Then we can move to improving research quality with Tavily AI or other solutions!
