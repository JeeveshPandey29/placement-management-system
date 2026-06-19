from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from auth import require_trainer
from schemas import AnalyticsSummary

router = APIRouter()


@router.get("", response_model=AnalyticsSummary)
def get_analytics(current_user: dict = Depends(require_trainer)):
    try:
        with get_db() as cur:
            cur.execute("SELECT COUNT(*) FROM pms_users WHERE role = 'student'")
            total_students = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM student_profiles WHERE status = 'placed'")
            placed_students = cur.fetchone()[0]

            placement_percentage = (placed_students / total_students * 100) if total_students > 0 else 0.0

            cur.execute("SELECT AVG(gpa) FROM student_profiles WHERE gpa > 0")
            avg = cur.fetchone()[0]
            average_gpa = float(avg) if avg else 0.0

            cur.execute("SELECT COUNT(*) FROM placement_drives")
            total_drives = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM colleges")
            total_colleges = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM batches")
            total_batches = cur.fetchone()[0]

        return {
            "total_students": total_students,
            "placed_students": placed_students,
            "placement_percentage": round(placement_percentage, 2),
            "average_gpa": round(average_gpa, 2),
            "total_drives": total_drives,
            "total_colleges": total_colleges,
            "total_batches": total_batches,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
