from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from database import get_db
from auth import require_admin, get_current_user
from schemas import CollegeOut

router = APIRouter()

@router.get("", response_model=List[CollegeOut])
def list_colleges(current_user: dict = Depends(get_current_user)):
    try:
        with get_db() as cur:
            cur.execute("SELECT id, name, location FROM colleges ORDER BY name ASC")
            rows = cur.fetchall()
            return [{"id": r[0], "name": r[1], "location": r[2]} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
