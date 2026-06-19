from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from database import get_db
from auth import require_admin, get_current_user
from schemas import CollegeCreate, CollegeOut

router = APIRouter()


@router.get("", response_model=List[CollegeOut])
def list_colleges(current_user: dict = Depends(get_current_user)):
    with get_db() as cur:
        cur.execute("SELECT id, name, location FROM colleges ORDER BY name")
        return [{"id": r[0], "name": r[1], "location": r[2]} for r in cur.fetchall()]


@router.post("", response_model=CollegeOut, status_code=status.HTTP_201_CREATED)
def add_college(payload: CollegeCreate, admin: dict = Depends(require_admin)):
    with get_db() as cur:
        cur.execute(
            "INSERT INTO colleges (name, location) VALUES (%s, %s) RETURNING id",
            (payload.name, payload.location)
        )
        cid = cur.fetchone()[0]
    return {"id": cid, "name": payload.name, "location": payload.location}


@router.delete("/{college_id}")
def delete_college(college_id: int, admin: dict = Depends(require_admin)):
    with get_db() as cur:
        cur.execute("DELETE FROM colleges WHERE id = %s RETURNING id", (college_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="College not found")
    return {"message": "College deleted"}
