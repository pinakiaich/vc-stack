# How to Start the FastAPI Backend

## Quick Start

To use the Deal Workspace (v2) features, you need to start the FastAPI backend server.

### Option 1: Using uvicorn directly

```bash
# Navigate to the project root
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"

# Start the FastAPI server
cd backend
uvicorn app.main:app --reload --port 8000
```

Or from the project root:
```bash
uvicorn backend.app.main:app --reload --port 8000
```

### Option 2: Using Python module

```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack/backend"
python -m uvicorn app.main:app --reload --port 8000
```

## Verify It's Running

Once started, you should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

You can verify by visiting:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Testing the v2 Endpoints

Once the server is running, you can test the endpoints:

```bash
# Create a deal
curl -X POST "http://localhost:8000/v2/deals" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Deal",
    "source": "referral",
    "owner": "John Doe",
    "sector": "SaaS",
    "stage": "Series A"
  }'

# List deals
curl "http://localhost:8000/v2/deals"

# Get specific deal
curl "http://localhost:8000/v2/deals/1"
```

Or use the interactive API docs at: http://localhost:8000/docs

## Running Both Frontend and Backend

You'll need **two terminal windows**:

**Terminal 1 - Backend:**
```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack/backend"
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
streamlit run streamlit_app.py
```

## Troubleshooting

### Port 8000 already in use
If port 8000 is already taken, use a different port:
```bash
uvicorn app.main:app --reload --port 8001
```

Then update the API_BASE_URL in streamlit_app.py (or make it configurable).

### Database not found
Make sure the database is initialized:
```bash
python backend/app/init_db.py
```

### Import errors
Make sure you're in the correct directory and all dependencies are installed:
```bash
pip install -r requirements.txt
```

## Notes

- The `--reload` flag enables auto-reload on code changes (useful for development)
- The backend runs on `http://localhost:8000` by default
- The Streamlit app connects to `http://localhost:8000` (defined in `API_BASE_URL`)
- CORS is enabled, so the frontend can connect to the backend
