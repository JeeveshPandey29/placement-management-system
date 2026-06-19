from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from database import get_db
from auth import require_student, require_trainer
from schemas import StudentProfileUpdate, StudentProfileOut

router = APIRouter()

@router.put("/profile", response_model=StudentProfileOut)
def update_student_profile(payload: StudentProfileUpdate, current_user: dict = Depends(require_student)):
    try:
        user_id = current_user["id"]
        with get_db() as cur:
            fields = []
            values = []
            
            update_map = {
                "roll_number": payload.roll_number,
                "college_id": payload.college_id,
                "branch": payload.branch,
                "gpa": payload.gpa,
                "resume_url": payload.resume_url,
                "skills": payload.skills,
                "status": payload.status
            }
            
            for key, val in update_map.items():
                if val is not None:
                    fields.append(f"{key} = %s")
                    values.append(val)
            
            if fields:
                values.append(user_id)
                query = f"UPDATE student_profiles SET {', '.join(fields)} WHERE user_id = %s"
                cur.execute(query, tuple(values))

            cur.execute("""
                SELECT sp.user_id, u.email, sp.roll_number, sp.college_id, c.name, sp.branch, sp.gpa, sp.resume_url, sp.skills, sp.status
                FROM student_profiles sp
                JOIN users u ON sp.user_id = u.id
                LEFT JOIN colleges c ON sp.college_id = c.id
                WHERE sp.user_id = %s
            """, (user_id,))
            
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Student profile not found")
            
            return {
                "user_id": row[0],
                "email": row[1],
                "roll_number": row[2],
                "college_id": row[3],
                "college_name": row[4],
                "branch": row[5],
                "gpa": row[6],
                "resume_url": row[7],
                "skills": row[8],
                "status": row[9]
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile", response_model=StudentProfileOut)
def get_own_student_profile(current_user: dict = Depends(require_student)):
    try:
        user_id = current_user["id"]
        with get_db() as cur:
            cur.execute("""
                SELECT sp.user_id, u.email, sp.roll_number, sp.college_id, c.name, sp.branch, sp.gpa, sp.resume_url, sp.skills, sp.status
                FROM student_profiles sp
                JOIN users u ON sp.user_id = u.id
                LEFT JOIN colleges c ON sp.college_id = c.id
                WHERE sp.user_id = %s
            """, (user_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Student profile not found")
            
            return {
                "user_id": row[0],
                "email": row[1],
                "roll_number": row[2],
                "college_id": row[3],
                "college_name": row[4],
                "branch": row[5],
                "gpa": row[6],
                "resume_url": row[7],
                "skills": row[8],
                "status": row[9]
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[StudentProfileOut])
def list_students(college_id: Optional[int] = None, status: Optional[str] = None, current_user: dict = Depends(require_trainer)):
    try:
        with get_db() as cur:
            query = """
                SELECT sp.user_id, u.email, sp.roll_number, sp.college_id, c.name, sp.branch, sp.gpa, sp.resume_url, sp.skills, sp.status
                FROM student_profiles sp
                JOIN users u ON sp.user_id = u.id
                LEFT JOIN colleges c ON sp.college_id = c.id
            """
            conditions = []
            values = []
            
            if college_id is not None:
                conditions.append("sp.college_id = %s")
                values.append(college_id)
            if status is not None:
                conditions.append("sp.status = %s")
                values.append(status)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY u.email ASC"
            
            cur.execute(query, tuple(values))
            rows = cur.fetchall()
            return [
                {
                    "user_id": r[0],
                    "email": r[1],
                    "roll_number": r[2],
                    "college_id": r[3],
                    "college_name": r[4],
                    "branch": r[5],
                    "gpa": r[6],
                    "resume_url": r[7],
                    "skills": r[8],
                    "status": r[9]
                }
                for r in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
