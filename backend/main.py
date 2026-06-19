from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import auth, colleges, students, attendance, assessments, drives, analytics

app = FastAPI(title="Student Placement Management System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to PMS Backend"}

app.include_router(auth.router, tags=["Authentication"])
app.include_router(colleges.router, prefix="/colleges", tags=["Colleges"])
app.include_router(students.router, prefix="/students", tags=["Student Profiles"])
app.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
app.include_router(assessments.router, prefix="/assessments", tags=["Assessments"])
app.include_router(drives.router, prefix="/drives", tags=["Placement Drives & Applications"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
