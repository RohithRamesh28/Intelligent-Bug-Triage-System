# routes/auth.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.models import users_collection, projects_collection
from utils.auth_utils import hash_password, verify_password, create_jwt_token
from bson import ObjectId
from datetime import datetime, timezone

router = APIRouter()

# === Pydantic models ===

class RegisterRequest(BaseModel):
    username: str
    password: str
    project_id: str  # Now we take project_id (not project_name)

class LoginRequest(BaseModel):
    username: str
    password: str

# === Register endpoint ===

@router.post("/register")
def register_user(data: RegisterRequest):
    username = data.username
    password = data.password
    project_id = data.project_id

    # Validate project_id exists
    project = projects_collection.find_one({"_id": ObjectId(project_id)})
    if not project:
        raise HTTPException(status_code=400, detail="Invalid project_id. Project not found.")

    # Check if username already exists in this project
    existing_user = users_collection.find_one({
        "username": username,
        "project_id": ObjectId(project_id)
    })
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists in this Project.")

    # Create new User
    password_hash = hash_password(password)
    user_doc = {
        "username": username,
        "password_hash": password_hash,
        "project_id": ObjectId(project_id),
        "created_at": datetime.now(timezone.utc)
    }
    user_id = users_collection.insert_one(user_doc).inserted_id

    # If project creator was None → update it now
    if project.get("creator_user_id") is None:
        projects_collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"creator_user_id": user_id}}
        )

    return {
        "message": "User registered successfully.",
        "user_id": str(user_id),
        "project_id": str(project_id)
    }
# === Login endpoint ===

@router.post("/login")
def login_user(data: LoginRequest):
    username = data.username
    password = data.password

    # Find user
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    # Verify password
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    project_id = user["project_id"]
    user_id = user["_id"]

    # Create JWT token
    token = create_jwt_token(str(user_id), str(project_id))

    return {"token": token, "user_id": str(user_id), "project_id": str(project_id)}
