from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from auth import require_trainer
from schemas import AnalyticsSummary

router = APIRouter()

@router.get("", response_model=AnalyticsSummary)
def get_placement_analytics(current_user: dict = Depends(require_trainer)):
    try:
        with get_db() as cur:
            # Total Students
            cur.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
            total_students = cur.fetchone()[0]

            # Placed Students
            cur.execute("SELECT COUNT(*) FROM student_profiles WHERE status = 'placed'")
            placed_students = cur.fetchone()[0]

            # Placement Percentage
            placement_percentage = (placed_students / total_students * 100) if total_students > 0 else 0.0

            # Average GPA
            cur.execute("SELECT AVG(gpa) FROM student_profiles WHERE gpa > 0")
            avg_gpa_row = cur.fetchone()
            average_gpa = float(avg_gpa_row[0]) if avg_gpa_row and avg_gpa_row[0] is not None else 0.0

            # Total Drives
            cur.execute("SELECT COUNT(*) FROM placement_drives")
            total_drives = cur.fetchone()[0]

            # Total Colleges
            cur.execute("SELECT COUNT(*) FROM colleges")
            total_colleges = cur.fetchone()[0]

        return {
            "total_students": total_students,
            "placed_students": placed_students,
            "placement_percentage": round(placement_percentage, 2),
            "average_gpa": round(average_gpa, 2),
            "total_drives": total_drives,
            "total_colleges": total_colleges
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

