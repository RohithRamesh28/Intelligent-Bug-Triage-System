# routes/project.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.models import projects_collection
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from utils.auth_utils import get_current_user_data
from bson import ObjectId
from db.models import file_analysis_collection
import os
from db.models import users_collection

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

    # Get distinct upload_ids for this project
    upload_ids = file_analysis_collection.distinct("upload_id", {"project_id": project_id})

    uploads = []
    for upload_id in upload_ids:
        # Find one document for this upload_id to get metadata
        first_doc = file_analysis_collection.find_one({"upload_id": upload_id})

        # Count how many documents (files) for this upload_id
        num_files = file_analysis_collection.count_documents({"upload_id": upload_id})

        # Get all bugs_sanity_checked from all documents of this upload_id
        all_docs = file_analysis_collection.find({"upload_id": upload_id})

        bugs_sanity_checked = []
        for doc in all_docs:
            bugs_sanity_checked.extend(doc.get("bugs_sanity_checked", []))

        # Collect file names
        file_names = [os.path.basename(doc.get("file", "")) for doc in file_analysis_collection.find({"upload_id": upload_id})]

        uploads.append({
            "upload_id": upload_id,
            "upload_description": first_doc.get("upload_description"),
            "original_filename": first_doc.get("original_filename"),
            "user_id": str(first_doc.get("user_id")),
            "username": first_doc.get("username"),
            "timestamp": first_doc.get("timestamp"),
            "num_files": num_files,
            "file_names": file_names,  
            "bugs_sanity_checked": bugs_sanity_checked
        })

    # Sort uploads by timestamp descending
    uploads.sort(key=lambda x: x["timestamp"], reverse=True)

    return {"project_id": str(user_data["project_id"]), "uploads": uploads}





@router.get("/project/user-stats")
def user_stats(user_data: dict = Depends(get_current_user_data)):
    project_id = ObjectId(user_data["project_id"])

    users = users_collection.find({"project_id": project_id})
    developers = 0
    team_leads = 0

    for user in users:
        role = user.get("role", "developer")
        if role == "team_lead":
            team_leads += 1
        else:
            developers += 1

    return {
        "developers": developers,
        "team_leads": team_leads
    }

@router.get("/project/my-uploads")
def my_uploads(user_data: dict = Depends(get_current_user_data)):
    project_id = ObjectId(user_data["project_id"])
    user_id = ObjectId(user_data["user_id"])

    # First → get distinct upload_ids for this user in this project
    upload_ids = file_analysis_collection.distinct(
        "upload_id", {"project_id": project_id, "user_id": user_id}
    )

    uploads = []
    for upload_id in upload_ids:
        # First try with project_id + user_id
        all_docs_cursor = file_analysis_collection.find({
            "project_id": project_id,
            "upload_id": upload_id,
            "user_id": user_id
        })

        files_data = []
        first_doc = None
        for doc in all_docs_cursor:
            if first_doc is None:
                first_doc = doc

            files_data.append(doc)

        # Fallback if no docs found
        if first_doc is None:
            print("[DEBUG] MyUploads fallback → trying without project_id")
            all_docs_cursor = file_analysis_collection.find({
                "upload_id": upload_id,
                "user_id": user_id
            })

            for doc in all_docs_cursor:
                if first_doc is None:
                    first_doc = doc
                files_data.append(doc)

        if first_doc is None:
            continue  # skip this upload_id if no docs found at all

        # Aggregate bugs
        bugs_sanity_checked = []
        for doc in files_data:
            bugs_sanity_checked.extend(doc.get("bugs_sanity_checked", []))

        # Build upload entry
        uploads.append({
    "upload_id": upload_id,
    "upload_description": first_doc.get("upload_description"),
    "original_filename": first_doc.get("original_filename"),
    "user_id": str(first_doc.get("user_id")),
    "username": first_doc.get("username"),
    "timestamp": first_doc.get("timestamp"),
    "num_files": len(files_data),
    "file_names": [os.path.basename(doc.get("file", "")) for doc in files_data],
    "bugs_sanity_checked": bugs_sanity_checked
})
    # Sort by timestamp descending
    uploads.sort(key=lambda x: x["timestamp"], reverse=True)

    return {"project_id": str(user_data["project_id"]), "uploads": uploads}



@router.get("/upload/{upload_id}")
def upload_details(upload_id: str, user_data: dict = Depends(get_current_user_data)):
    project_id = ObjectId(user_data["project_id"])

    # First → try with project_id filter (normal case)
    all_docs_cursor = file_analysis_collection.find({
        "project_id": project_id,
        "upload_id": upload_id
    })

    files_data = []
    first_doc = None
    for doc in all_docs_cursor:
        if first_doc is None:
            first_doc = doc

        files_data.append({
            "file": doc.get("file"),
            "original_filename": doc.get("original_filename"),
            "bugs_original": doc.get("bugs_original", []),
            "bugs_sanity_checked": doc.get("bugs_sanity_checked", []),
            "optimizations_original": doc.get("optimizations_original", []),
            "optimizations_sanity_checked": doc.get("optimizations_sanity_checked", [])
        })

    # If no documents found → fallback → try without project_id (for old data)
    if first_doc is None:
        print("[DEBUG] No docs found with project_id → retrying without project_id")
        all_docs_cursor = file_analysis_collection.find({
            "upload_id": upload_id
        })

        for doc in all_docs_cursor:
            if first_doc is None:
                first_doc = doc

            files_data.append({
                "file": doc.get("file"),
                "original_filename": doc.get("original_filename"),
                "bugs_original": doc.get("bugs_original", []),
                "bugs_sanity_checked": doc.get("bugs_sanity_checked", []),
                "optimizations_original": doc.get("optimizations_original", []),
                "optimizations_sanity_checked": doc.get("optimizations_sanity_checked", [])
            })

    if first_doc is None:
        return {"error": "Upload not found"}, 404

    # Build full upload details response
    response = {
        "upload_id": upload_id,
        "upload_description": first_doc.get("upload_description"),
        "username": first_doc.get("username"),
        "user_id": str(first_doc.get("user_id")),
        "timestamp": first_doc.get("timestamp"),
        "num_files": len(files_data),
        "files": files_data
    }

    return response
# === GET /project/{project_id} ===

@router.get("/project/{project_id}")
def get_project_by_id(project_id: str):
    try:
        project = projects_collection.find_one({"_id": ObjectId(project_id)})

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        return {
            "project_id": str(project["_id"]),
            "project_name": project.get("project_name", "Unnamed Project"),
            "created_at": project.get("created_at"),
            "creator_user_id": str(project.get("creator_user_id")) if project.get("creator_user_id") else None,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

