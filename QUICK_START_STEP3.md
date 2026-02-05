# Quick Start Guide for Step 3 (Deal Workspace)

## Prerequisites Checklist

Before restarting Streamlit, make sure:

- [x] SQLAlchemy is installed: `pip3 install sqlalchemy`
- [ ] FastAPI backend is running on port 8000
- [ ] Database is initialized (if first time)

## Step-by-Step

### 1. Start the FastAPI Backend (Terminal 1)

```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack/backend"
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

**Keep this terminal running!**

### 2. Verify Backend is Working

In a new terminal, test the health endpoint:

```bash
curl http://localhost:8000/health
```

Should return: `{"status":"ok"}`

Or visit in browser: http://localhost:8000/health

### 3. Restart Streamlit App (Terminal 2)

```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
streamlit run streamlit_app.py
```

### 4. Use Deal Workspace

Once Streamlit is running:

1. **Open the sidebar** - You'll see "💼 Deal Workspace (v2)" section
2. **Create a deal**:
   - Click "➕ Create New Deal"
   - Enter a deal name (required)
   - Optionally fill other fields
   - Click "Create Deal"
3. **View deal metadata** - The selected deal info appears in the main content area

## If You See Connection Errors

If Streamlit shows "Could not connect to API":
- Make sure the backend is running (check Terminal 1)
- Verify health endpoint works: `curl http://localhost:8000/health`
- Check that both servers are on correct ports (8000 for backend, 8501 for Streamlit)

## Quick Test

After both servers are running, you should be able to:
1. See "💼 Deal Workspace (v2)" in the sidebar
2. Create a new deal successfully
3. See the deal metadata displayed in the main area
