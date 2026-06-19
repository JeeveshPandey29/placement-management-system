from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from database import get_db
from auth import require_trainer, get_current_user
from schemas import ClassCreate, ClassOut

router = APIRouter()


def _row_to_class(r) -> dict:
    return {
        "id": r[0], "batch_id": r[1], "batch_name": r[2],
        "title": r[3], "description": r[4],
        "class_date": r[5],
        "start_time": str(r[6]) if r[6] else None,
        "end_time": str(r[7]) if r[7] else None,
        "location": r[8]
    }


# ── Create class ───────────────────────────────────────────────────────────────
@router.post("", response_model=ClassOut, status_code=status.HTTP_201_CREATED)
def create_class(payload: ClassCreate, trainer: dict = Depends(require_trainer)):
    with get_db() as cur:
        cur.execute("SELECT id FROM batches WHERE id = %s", (payload.batch_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Batch not found")
        cur.execute("""
            INSERT INTO classes (batch_id, title, description, class_date, start_time, end_time, location)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (payload.batch_id, payload.title, payload.description, payload.class_date,
              payload.start_time, payload.end_time, payload.location))
        cid = cur.fetchone()[0]
        cur.execute("""
            SELECT c.id, c.batch_id, b.name, c.title, c.description,
                   c.class_date, c.start_time, c.end_time, c.location
            FROM classes c JOIN batches b ON c.batch_id = b.id
            WHERE c.id = %s
        """, (cid,))
        row = cur.fetchone()
    return _row_to_class(row)


# ── List classes ───────────────────────────────────────────────────────────────
@router.get("", response_model=List[ClassOut])
def list_classes(batch_id: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    with get_db() as cur:
        if current_user["role"] == "student":
            # only show classes for batches the student belongs to
            query = """
                SELECT c.id, c.batch_id, b.name, c.title, c.description,
                       c.class_date, c.start_time, c.end_time, c.location
                FROM classes c
                JOIN batches b ON c.batch_id = b.id
                JOIN batch_students bs ON b.id = bs.batch_id
                WHERE bs.student_id = %s
            """
            params = [current_user["id"]]
            if batch_id:
                query += " AND c.batch_id = %s"
                params.append(batch_id)
            query += " ORDER BY c.class_date DESC, c.start_time"
            cur.execute(query, params)
        else:
            query = """
                SELECT c.id, c.batch_id, b.name, c.title, c.description,
                       c.class_date, c.start_time, c.end_time, c.location
                FROM classes c JOIN batches b ON c.batch_id = b.id
            """
            params = []
            if batch_id:
                query += " WHERE c.batch_id = %s"
                params.append(batch_id)
            query += " ORDER BY c.class_date DESC, c.start_time"
            cur.execute(query, params)
        return [_row_to_class(r) for r in cur.fetchall()]


# ── Delete class ───────────────────────────────────────────────────────────────
@router.delete("/{class_id}")
def delete_class(class_id: int, trainer: dict = Depends(require_trainer)):
    with get_db() as cur:
        cur.execute("DELETE FROM classes WHERE id = %s RETURNING id", (class_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Class not found")
    return {"message": "Class deleted"}
