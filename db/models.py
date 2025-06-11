# db/models.py

from bson import ObjectId
from .mongo_client import client
from pymongo import ASCENDING
from datetime import datetime, timezone

db = client["bug_triage_db"]

# === Collections ===

users_collection = db["users"]
projects_collection = db["projects"]
file_analysis_collection = db["file_analysis"]

# === Indexes ===

users_collection.create_index(
    [("username", ASCENDING), ("project_id", ASCENDING)],
    unique=True
)

projects_collection.create_index(
    [("project_name", ASCENDING)],
    unique=True
)

# === Save Upload function ===

def save_to_mongo(upload_id, file_name, parsed_data, user_id, project_id, original_name=None):
    doc = {
        "upload_id": upload_id,
        "file": file_name,
        "original_filename": original_name,
        "bugs_original": parsed_data["bugs_original"],
        "bugs_sanity_checked": parsed_data["bugs_sanity_checked"],
        "optimizations_original": parsed_data["optimizations_original"],
        "optimizations_sanity_checked": parsed_data["optimizations_sanity_checked"],
        "user_id": ObjectId(user_id),        # new → saves user_id
        "project_id": ObjectId(project_id),  # new → saves project_id
        "timestamp": datetime.now(timezone.utc)
    }

    file_analysis_collection.update_one(
        {"upload_id": upload_id, "file": file_name},
        {"$set": doc},
        upsert=True
    )

    print(f"[MongoDB] Saved analysis for file: {file_name} (upload_id={upload_id}) original={original_name} user_id={user_id} project_id={project_id}")
