# utils/auth_utils.py

from datetime import datetime, timedelta, timezone
from passlib.hash import bcrypt
import jwt
import os
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
load_dotenv()


JWT_SECRET = os.getenv("JWT_SECRET", "fallback_secret")  
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_MINUTES = 60 * 24  


def hash_password(password: str) -> str:
    return bcrypt.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.verify(password, password_hash)


def create_jwt_token(user_id: str, project_id: str, username: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "project_id": project_id,
        "username": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXP_DELTA_MINUTES)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def decode_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")


bearer_scheme = HTTPBearer()

def get_current_user_data(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "user_id": payload["user_id"],
            "project_id": payload["project_id"],
            "username": payload.get("username", "Unknown"),
            "role": payload.get("role", "developer")
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
