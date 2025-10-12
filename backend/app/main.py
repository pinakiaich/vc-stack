from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="VC Stack API (MVP)")

# CORS lets a frontend (later) call this server from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # keep open in dev; we’ll lock down later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# A simple health-check route to confirm the server is alive
@app.get("/health")
def health():
    return {"status": "ok"}
