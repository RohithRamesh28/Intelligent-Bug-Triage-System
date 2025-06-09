# main.py

from fastapi import FastAPI
from routes import upload, progress_ws,file_bugs
from dotenv import load_dotenv
import os

# ✅ Load environment variables from .env
load_dotenv()

# print("Loaded OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
# ✅ Initialize FastAPI app
app = FastAPI(
    title="Intelligent Bug Triage System",
    version="1.0.0"
)

# ✅ Register your routes
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(progress_ws.router, tags=["WebSocket"])
app.include_router(file_bugs.router, tags=["File Bugs"])
# ✅ Optional root route — for testing
@app.get("/")
async def root():
    return {"message": "Welcome to Intelligent Bug Triage System API 🚀"}

