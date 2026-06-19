from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from database import get_db
from auth import require_trainer, require_student
from schemas import AttendanceRecord, AttendanceOut

router = APIRouter()

@router.post("", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
def record_attendance(payload: AttendanceRecord, trainer_user: dict = Depends(require_trainer)):
    try:
        with get_db() as cur:
            # Verify student exists and is indeed a student
            cur.execute("SELECT role FROM users WHERE id = %s", (payload.student_id,))
            row = cur.fetchone()
            if not row or row[0] != "student":
                raise HTTPException(status_code=400, detail="Invalid student ID")
            
            cur.execute(
                """INSERT INTO attendance (student_id, date, status, session_name)
                   VALUES (%s, %s, %s, %s) RETURNING id""",
                (payload.student_id, payload.date, payload.status, payload.session_name)
            )
            attendance_id = cur.fetchone()[0]
            
            cur.execute("SELECT email FROM users WHERE id = %s", (payload.student_id,))
            student_email = cur.fetchone()[0]
            
        return {
            "id": attendance_id,
            "student_id": payload.student_id,
            "student_email": student_email,
            "date": payload.date,
            "status": payload.status,
            "session_name": payload.session_name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[AttendanceOut])
def get_attendance_records(student_id: Optional[int] = None, trainer_user: dict = Depends(require_trainer)):
    try:
        with get_db() as cur:
            query = """
                SELECT a.id, a.student_id, u.email, a.date, a.status, a.session_name
                FROM attendance a
                JOIN users u ON a.student_id = u.id
            """
            values = []
            if student_id is not None:
                query += " WHERE a.student_id = %s"
                values.append(student_id)
                
            query += " ORDER BY a.date DESC, a.id DESC"
            cur.execute(query, tuple(values))
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "student_id": r[1],
                    "student_email": r[2],
                    "date": r[3],
                    "status": r[4],
                    "session_name": r[5]
                }
                for r in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my", response_model=List[AttendanceOut])
def get_my_attendance(current_user: dict = Depends(require_student)):
    try:
        student_id = current_user["id"]
        with get_db() as cur:
            cur.execute(
                """SELECT a.id, a.student_id, u.email, a.date, a.status, a.session_name
                   FROM attendance a
                   JOIN users u ON a.student_id = u.id
                   WHERE a.student_id = %s
                   ORDER BY a.date DESC""",
                (student_id,)
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "student_id": r[1],
                    "student_email": r[2],
                    "date": r[3],
                    "status": r[4],
                    "session_name": r[5]
                }
                for r in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
