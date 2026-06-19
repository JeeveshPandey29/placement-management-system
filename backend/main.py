from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import auth, colleges, students, attendance, assessments, drives, analytics, batches, classes, notifications

app = FastAPI(title="PMS 3.0 — Placement Management System API", version="3.0.0")

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
    return {"message": "PMS 3.0 Backend", "version": "3.0.0", "docs": "/docs"}


app.include_router(auth.router, tags=["Authentication & Admin"])
app.include_router(colleges.router, prefix="/colleges", tags=["Colleges"])
app.include_router(batches.router, prefix="/batches", tags=["Batches"])
app.include_router(classes.router, prefix="/classes", tags=["Classes"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(students.router, prefix="/students", tags=["Student Profiles"])
app.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
app.include_router(assessments.router, prefix="/assessments", tags=["Assessments"])
app.include_router(drives.router, prefix="/drives", tags=["Placement Drives"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
