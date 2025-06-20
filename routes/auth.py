from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.models import users_collection, projects_collection
from utils.auth_utils import hash_password, verify_password, create_jwt_token
from bson import ObjectId
from datetime import datetime, timezone

router = APIRouter()



class RegisterRequest(BaseModel):
    username: str
    password: str
    project_id: str
    role: str

class LoginRequest(BaseModel):
    username: str
    password: str
    project_id: str
    role: str


@router.post("/register")
def register_user(data: RegisterRequest):
    username = data.username.strip().lower()
    password = data.password
    project_id = data.project_id
    role = data.role

    project = projects_collection.find_one({"_id": ObjectId(project_id)})
    if not project:
        raise HTTPException(status_code=400, detail="Invalid project_id. Project not found.")

    existing_user = users_collection.find_one({
        "username": username,
        "project_id": ObjectId(project_id),
        "role": role
    })
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists for this role in this project.")

    password_hash = hash_password(password)
    user_doc = {
        "username": username,
        "password_hash": password_hash,
        "project_id": ObjectId(project_id),
        "role": role,
        "created_at": datetime.now(timezone.utc)
    }

    user_id = users_collection.insert_one(user_doc).inserted_id

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



@router.post("/login")
def login_user(data: LoginRequest):
    username = data.username.strip().lower()
    password = data.password
    project_id = data.project_id
    role = data.role

    user = users_collection.find_one({
        "username": username,
        "project_id": ObjectId(project_id),
        "role": role
    })

    if not user:
        raise HTTPException(status_code=404, detail="User not found with this role and project.")

    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    token = create_jwt_token(
        user_id=str(user["_id"]),
        project_id=str(project_id),
        username=username,
        role=role
    )

    return {
        "token": token,
        "user_id": str(user["_id"]),
        "project_id": str(project_id),
        "role": role,
        "username": username 
    }
