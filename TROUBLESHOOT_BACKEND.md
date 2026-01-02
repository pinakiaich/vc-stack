# Troubleshooting Backend Connection Issues

## Issue: `/health` endpoint not returning "ok"

If you're getting connection errors or the health endpoint isn't working, follow these steps:

## Step 1: Check if Dependencies are Installed

The backend requires several Python packages. Make sure they're installed:

```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
pip install -r requirements.txt
```

Key dependencies needed:
- `fastapi`
- `uvicorn`
- `sqlalchemy`
- `pydantic`

## Step 2: Verify Backend Code Imports

Test if the backend code can be imported:

```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack/backend"
python3 -c "from app.main import app; print('✅ Backend imports OK')"
```

If this fails, you'll see the specific import error that needs to be fixed.

## Step 3: Initialize Database

Make sure the database is created:

```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
python backend/app/init_db.py
```

This creates the SQLite database file (`local.db`) with all necessary tables.

## Step 4: Start the Backend Server

Start the FastAPI server:

```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack/backend"
uvicorn app.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Will watch for changes in these directories: ['/path/to/vc-stack/backend']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Step 5: Test the Health Endpoint

Once the server is running, test it:

**Using curl:**
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{"status":"ok"}
```

**Using browser:**
Visit: http://localhost:8000/health

**Using Python:**
```python
import requests
response = requests.get("http://localhost:8000/health")
print(response.json())  # Should print: {'status': 'ok'}
```

## Common Issues

### Issue 1: "Connection refused"
**Symptom:** `curl: (7) Failed to connect to localhost port 8000`

**Cause:** Backend server is not running

**Solution:** Start the server (Step 4 above)

### Issue 2: "ModuleNotFoundError: No module named 'sqlalchemy'"
**Symptom:** Import error when starting server

**Cause:** Dependencies not installed

**Solution:** 
```bash
pip install -r requirements.txt
```

### Issue 3: Port 8000 already in use
**Symptom:** `ERROR:    [Errno 48] Address already in use`

**Cause:** Another process is using port 8000

**Solution:**
- Find and kill the process using port 8000:
  ```bash
  lsof -ti:8000 | xargs kill -9
  ```
- Or use a different port:
  ```bash
  uvicorn app.main:app --reload --port 8001
  ```
  Then update `API_BASE_URL` in `streamlit_app.py` to `http://localhost:8001`

### Issue 4: Database errors on startup
**Symptom:** Errors related to database tables

**Solution:** Run database initialization:
```bash
python backend/app/init_db.py
```

### Issue 5: Import errors in backend code
**Symptom:** Errors when starting uvicorn about missing modules

**Solution:** Make sure you're in the correct directory and all imports are correct:
- Start server from `backend/` directory: `uvicorn app.main:app --reload`
- Or from project root: `uvicorn backend.app.main:app --reload`

## Verification Checklist

Before reporting issues, verify:

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database initialized (`python backend/app/init_db.py`)
- [ ] Server starts without errors
- [ ] Health endpoint returns `{"status": "ok"}`
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] Port 8000 is available (not used by another process)

## Getting Help

If the health endpoint still doesn't work:

1. Check the server logs for error messages
2. Verify all dependencies are installed correctly
3. Make sure you're using Python 3.8+
4. Check that the database file exists (`local.db` in project root)
5. Try starting with verbose logging:
   ```bash
   uvicorn app.main:app --reload --port 8000 --log-level debug
   ```
