# main.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from routes import upload, progress_ws, file_bugs
from dotenv import load_dotenv
import os
from routes import auth
from routes import project



# ✅ Load environment variables from .env
load_dotenv()

# ✅ Initialize FastAPI app
app = FastAPI(
    title="Intelligent Bug Triage System",
    version="1.0.0"
)

# ✅ Enable CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # allow frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register your routes
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(progress_ws.router, tags=["WebSocket"])
app.include_router(file_bugs.router, tags=["File Bugs"])
app.include_router(auth.router, tags=["Auth"])
app.include_router(project.router, tags=["Project"])


# ✅ Optional root route — for testing
@app.get("/")
async def root():
    return {"message":"Welcome to Intelligent Bug Triage System API 🚀"}
