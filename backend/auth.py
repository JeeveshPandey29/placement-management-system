import os
import time
from typing import Dict
from jose import jwt
from dotenv import load_dotenv
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from database import get_db

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set. Check your .env file.")

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user_id: int, role: str) -> Dict[str, str]:
    payload = {"user_id": user_id, "role": role, "expires": time.time() + 28800}  # 8h
    return {"token": jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM), "token_type": "Bearer"}


def decode_jwt(token: str) -> dict:
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return data if data["expires"] > time.time() else None
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    payload = decode_jwt(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token expired")
    uid = int(payload["user_id"])
    with get_db() as cur:
        cur.execute(
            "SELECT id, email, role, full_name, must_change_password FROM pms_users WHERE id = %s",
            (uid,)
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    return {"id": row[0], "email": row[1], "role": row[2],
            "full_name": row[3], "must_change_password": row[4]}


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def require_trainer(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] not in ("trainer", "admin"):
        raise HTTPException(status_code=403, detail="Trainer or Admin access required")
    return user


def require_student(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "student":
        raise HTTPException(status_code=403, detail="Student access required")
    return user
