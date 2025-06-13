# routes/me.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from db.models import users_collection, projects_collection
from utils.auth_utils import get_current_user_data, hash_password
from bson import ObjectId
from typing import Optional  # ✅ added for compatibility

router = APIRouter()

# === Pydantic model for PUT ===

class UpdateMeRequest(BaseModel):
    new_username: Optional[str] = None
    new_password: Optional[str] = None

# === GET /me ===

@router.get("/me")
def get_me(user_data: dict = Depends(get_current_user_data)):
    user_id = ObjectId(user_data["user_id"])
    project_id = ObjectId(user_data["project_id"])

    user = users_collection.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    project = projects_collection.find_one({"_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    return {
        "username": user["username"],
        "project_name": project["project_name"]
    }

# === PUT /me ===

@router.put("/me")
def update_me(data: UpdateMeRequest, user_data: dict = Depends(get_current_user_data)):
    user_id = ObjectId(user_data["user_id"])
    project_id = ObjectId(user_data["project_id"])

    user = users_collection.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    updates = {}

    # Handle username change
    if data.new_username:
        # Check if username already exists in this project
        existing_user = users_collection.find_one({
            "username": data.new_username,
            "project_id": project_id,
            "_id": {"$ne": user_id}  # exclude self
        })
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists in this Project.")

        updates["username"] = data.new_username

    # Handle password change
    if data.new_password:
        updates["password_hash"] = hash_password(data.new_password)

    # Apply updates
    if updates:
        users_collection.update_one(
            {"_id": user_id},
            {"$set": updates}
        )

    return {"message": "Profile updated successfully."}
