from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from database import get_db
from auth import require_trainer, require_student
from schemas import AttendanceRecord, AttendanceOut

router = APIRouter()


def _row_to_att(r) -> dict:
    return {
        "id": r[0], "student_id": r[1], "student_email": r[2],
        "student_name": r[3], "date": r[4], "status": r[5],
        "session_name": r[6], "batch_id": r[7], "class_id": r[8]
    }


@router.post("", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
def record_attendance(payload: AttendanceRecord, trainer: dict = Depends(require_trainer)):
    with get_db() as cur:
        cur.execute("SELECT role FROM pms_users WHERE id = %s", (payload.student_id,))
        row = cur.fetchone()
        if not row or row[0] != "student":
            raise HTTPException(status_code=400, detail="Invalid student ID")
        cur.execute("""
            INSERT INTO attendance (student_id, batch_id, class_id, date, status, session_name)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """, (payload.student_id, payload.batch_id, payload.class_id,
              payload.date, payload.status, payload.session_name))
        aid = cur.fetchone()[0]
        cur.execute("SELECT email, full_name FROM pms_users WHERE id = %s", (payload.student_id,))
        urow = cur.fetchone()
    return {
        "id": aid, "student_id": payload.student_id,
        "student_email": urow[0], "student_name": urow[1],
        "date": payload.date, "status": payload.status,
        "session_name": payload.session_name,
        "batch_id": payload.batch_id, "class_id": payload.class_id
    }


@router.get("", response_model=List[AttendanceOut])
def get_attendance(
    student_id: Optional[int] = None,
    batch_id: Optional[int] = None,
    trainer: dict = Depends(require_trainer)
):
    conditions, vals = [], []
    if student_id:
        conditions.append("a.student_id = %s"); vals.append(student_id)
    if batch_id:
        conditions.append("a.batch_id = %s"); vals.append(batch_id)
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    with get_db() as cur:
        cur.execute(f"""
            SELECT a.id, a.student_id, u.email, u.full_name,
                   a.date, a.status, a.session_name, a.batch_id, a.class_id
            FROM attendance a
            JOIN pms_users u ON a.student_id = u.id
            {where} ORDER BY a.date DESC, a.id DESC
        """, vals)
        return [_row_to_att(r) for r in cur.fetchall()]


@router.get("/my", response_model=List[AttendanceOut])
def get_my_attendance(student: dict = Depends(require_student)):
    with get_db() as cur:
        cur.execute("""
            SELECT a.id, a.student_id, u.email, u.full_name,
                   a.date, a.status, a.session_name, a.batch_id, a.class_id
            FROM attendance a
            JOIN pms_users u ON a.student_id = u.id
            WHERE a.student_id = %s ORDER BY a.date DESC
        """, (student["id"],))
        return [_row_to_att(r) for r in cur.fetchall()]


@router.delete("/{attendance_id}")
def delete_attendance(attendance_id: int, trainer: dict = Depends(require_trainer)):
    with get_db() as cur:
        cur.execute("DELETE FROM attendance WHERE id = %s RETURNING id", (attendance_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Record not found")
    return {"message": "Record deleted"}
