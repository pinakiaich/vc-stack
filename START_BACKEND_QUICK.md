# 🚀 Quick Start: Backend Required for Deal Workspace

## ⚠️ Important: You Need Two Terminals Running

The Deal Workspace features require the FastAPI backend to be running.

## Step 1: Start Backend (Terminal 1)

Open a terminal and run:

```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack/backend"
uvicorn app.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

**Keep this terminal running!** Don't close it.

## Step 2: Verify Backend is Running

In a new terminal (or browser), test:

```bash
curl http://localhost:8000/health
```

Should return: `{"status":"ok"}`

Or visit in browser: http://localhost:8000/health

## Step 3: Start Streamlit (Terminal 2)

Open a **second terminal** and run:

```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
streamlit run streamlit_app.py
```

## Step 4: Use the Features

Now you can:
1. **Filter companies** → Top 10 will auto-create as deals (if backend is running)
2. **Select deals** from sidebar dropdown
3. **Conduct research** on selected deals

## Troubleshooting

### "Connection refused" Error

This means the backend is not running. Go back to **Step 1** and start the backend.

### Port 8000 Already in Use

If port 8000 is busy:
```bash
# Use a different port
uvicorn app.main:app --reload --port 8001
```

Then update `API_BASE_URL` in `streamlit_app.py` (line ~75) to `http://localhost:8001`

### Database Not Found

Initialize the database first:
```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
python backend/app/init_db.py
```

## Quick Reference

**Terminal 1 (Backend):**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```bash
streamlit run streamlit_app.py
```

**Health Check:**
```bash
curl http://localhost:8000/health
```
