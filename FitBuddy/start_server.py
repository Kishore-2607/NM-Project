import uvicorn
from app.main import app

if __name__ == "__main__":
    print("Starting FitBuddy server on http://127.0.0.1:8000 and http://localhost:8000 ...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
