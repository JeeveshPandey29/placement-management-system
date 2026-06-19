from fastapi import APIRouter, Depends, HTTPException, status
from database import get_db
from auth import hash_password, verify_password, create_token, get_current_user
from schemas import UserRegister, UserLogin, UserOut

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister):
    try:
        with get_db() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (payload.email,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Email already registered")
            
            hashed = hash_password(payload.password)
            cur.execute(
                "INSERT INTO users (email, password, role) VALUES (%s, %s, %s) RETURNING id",
                (payload.email, hashed, payload.role),
            )
            user_id = cur.fetchone()[0]

            if payload.role == "student":
                cur.execute(
                    "INSERT INTO student_profiles (user_id, college_id, status) VALUES (%s, 1, %s)",
                    (user_id, "unplaced")
                )
                
        return {"id": user_id, "email": payload.email, "role": payload.role}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
def login(payload: UserLogin):
    try:
        with get_db() as cur:
            cur.execute("SELECT id, password, role FROM users WHERE email = %s", (payload.email,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            user_id, hashed, role = row[0], row[1], row[2]
            if not verify_password(payload.password, hashed):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            token = create_token(user_id, role)
        return token
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me", response_model=UserOut)
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
