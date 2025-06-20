from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from routes import upload, progress_ws, file_bugs
from dotenv import load_dotenv
import os
from routes import auth
from routes import project
from routes import me

load_dotenv()

app = FastAPI(
    title="Intelligent Bug Triage System",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(progress_ws.router, tags=["WebSocket"])
app.include_router(file_bugs.router, tags=["File Bugs"])
app.include_router(auth.router, tags=["Auth"])
app.include_router(project.router, tags=["Project"])
app.include_router(me.router, tags=["Me"])



@app.get("/")
async def root():
    return {"message":"Welcome to Intelligent Bug Triage System API "}
