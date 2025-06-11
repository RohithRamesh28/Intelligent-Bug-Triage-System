# routes/project.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.models import projects_collection
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from utils.auth_utils import get_current_user_data
from db.models import file_analysis_collection
from bson import ObjectId

router = APIRouter()

# === Pydantic models ===

class CreateProjectRequest(BaseModel):
    project_name: str

# === GET /projects/list ===

@router.get("/projects/list")
def list_projects():
    projects = projects_collection.find({}, {"project_name": 1})
    project_list = [
        {"project_id": str(p["_id"]), "project_name": p["project_name"]}
        for p in projects
    ]
    return {"projects": project_list}

# === POST /projects/create ===

@router.post("/projects/create")
def create_project(data: CreateProjectRequest):
    project_name = data.project_name.strip()

    if not project_name:
        raise HTTPException(status_code=400, detail="Project name cannot be empty.")

    # Check if project already exists
    existing = projects_collection.find_one({"project_name": project_name})
    if existing:
        raise HTTPException(status_code=400, detail="Project name already exists.")

    # Create project
    project_doc = {
        "project_name": project_name,
        "creator_user_id": None,  # no user yet linked
        "created_at": datetime.now(timezone.utc)
    }
    project_id = projects_collection.insert_one(project_doc).inserted_id

    return {
        "message": "Project created successfully.",
        "project_id": str(project_id),
        "project_name": project_name
    }

# === Project Dashboard ===

@router.get("/project/dashboard")
def project_dashboard(user_data: dict = Depends(get_current_user_data)):
    project_id = ObjectId(user_data["project_id"])

    uploads_cursor = file_analysis_collection.find({"project_id": project_id})
    uploads = []
    for upload in uploads_cursor:
        uploads.append({
            "upload_id": upload.get("upload_id"),
            "file": upload.get("file"),
            "original_filename": upload.get("original_filename"),
            "bugs_original": upload.get("bugs_original"),
            "bugs_sanity_checked": upload.get("bugs_sanity_checked"),
            "optimizations_original": upload.get("optimizations_original"),
            "optimizations_sanity_checked": upload.get("optimizations_sanity_checked"),
            "timestamp": upload.get("timestamp")
        })

    return {"project_id": user_data["project_id"], "uploads": uploads}

# === Personal Upload History ===

@router.get("/project/my-uploads")
def my_uploads(user_data: dict = Depends(get_current_user_data)):
    project_id = ObjectId(user_data["project_id"])
    user_id = ObjectId(user_data["user_id"])

    uploads_cursor = file_analysis_collection.find({
        "project_id": project_id,
        "user_id": user_id
    })
    uploads = []
    for upload in uploads_cursor:
        uploads.append({
            "upload_id": upload.get("upload_id"),
            "file": upload.get("file"),
            "original_filename": upload.get("original_filename"),
            "bugs_original": upload.get("bugs_original"),
            "bugs_sanity_checked": upload.get("bugs_sanity_checked"),
            "optimizations_original": upload.get("optimizations_original"),
            "optimizations_sanity_checked": upload.get("optimizations_sanity_checked"),
            "timestamp": upload.get("timestamp")
        })

    return {
        "project_id": user_data["project_id"],
        "user_id": user_data["user_id"],
        "uploads": uploads
    }
