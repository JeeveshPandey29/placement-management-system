# PMS 3.0 — Postman Test Cases

**Base URL:** `https://placement-management-system-u48x.onrender.com`

> Set `{{token}}` as a Postman variable after login. Add header `Authorization: Bearer {{token}}` to all authenticated requests.

---

## 1. SETUP

### 1.1 Create First Admin (one-time only)
```
POST /setup/admin
Body: {
  "email": "jeevesh.pandey@pms.com",
  "password": "Admin@123",
  "full_name": "Jeevesh Pandey"
}
Expected: 201 — { "id": 1, "email": "...", "role": "admin" }
```

---

## 2. AUTHENTICATION

### 2.1 Login
```
POST /login
Body: { "email": "jeevesh.pandey@pms.com", "password": "Admin@123" }
Expected: 200 — { "token": "...", "token_type": "Bearer", "must_change_password": false }
```

### 2.2 Get Current User
```
GET /me
Auth: Bearer {{token}}
Expected: 200 — { "id": 1, "email": "...", "role": "admin" }
```

### 2.3 Set Password (first login)
```
POST /set-password
Auth: Bearer {{token}}
Body: { "new_password": "MyNewPass@123" }
Expected: 200 — { "message": "Password updated successfully" }
```

### 2.4 Change Password
```
POST /change-password
Auth: Bearer {{token}}
Body: { "old_password": "Admin@123", "new_password": "Admin@456" }
Expected: 200 — { "message": "Password changed successfully" }
```

### 2.5 Forgot Password
```
POST /forgot-password
Body: { "email": "jeevesh.pandey@pms.com" }
Expected: 200 — { "reset_token": "abc123..." }
```

### 2.6 Reset Password
```
POST /reset-password
Body: { "token": "<from 2.5>", "new_password": "Admin@123" }
Expected: 200 — { "message": "Password reset successfully. Please log in." }
```

---

## 3. ADMIN — USER MANAGEMENT

### 3.1 Create Trainer
```
POST /admin/users
Auth: Bearer {{token}}
Body: {
  "email": "vijay.bhilare@pms.com",
  "full_name": "Vijay Bhilare",
  "role": "trainer"
}
Expected: 201
Default password = "vijay.bhilare" (email prefix)
```

### 3.2 Create Student
```
POST /admin/users
Auth: Bearer {{token}}
Body: {
  "email": "krish.gupta@student.com",
  "full_name": "Krish Gupta",
  "role": "student",
  "enrollment_number": "CSE2024001",
  "branch": "Computer Science"
}
Expected: 201
Default password = "CSE2024001" (enrollment number)
```

### 3.3 Bulk Upload via CSV
```
POST /admin/users/bulk
Auth: Bearer {{token}}
Body: form-data, key="file", type=File
CSV format:
  full_name,email,role,enrollment_number,branch
  Aarav Sharma,aarav.sharma@student.com,student,CSE2024002,Computer Science
  Atharva Jagtap,atharva.jagtap@pms.com,trainer,,
Expected: 200 — { "created": 2, "skipped_duplicates": 0, "errors": [] }
```

### 3.4 List All Users
```
GET /admin/users
Auth: Bearer {{token}}
Expected: 200 — array of users

GET /admin/users?role=student
Expected: 200 — only students
```

### 3.5 Delete User
```
DELETE /admin/users/5
Auth: Bearer {{token}}
Expected: 200 — { "message": "User deleted" }
```

---

## 4. COLLEGES

### 4.1 List Colleges
```
GET /colleges
Auth: Bearer {{token}}
Expected: 200 — [{ "id": 1, "name": "MITADT UNIVERSITY", "location": "Pune" }]
```

### 4.2 Add College
```
POST /colleges
Auth: Bearer {{token}}
Body: { "name": "VIT Pune", "location": "Pune" }
Expected: 201
```

### 4.3 Delete College
```
DELETE /colleges/2
Auth: Bearer {{token}}
Expected: 200
```

---

## 5. BATCHES

### 5.1 Create Batch
```
POST /batches
Auth: Bearer {{token}}
Body: { "name": "SD1", "branch": "Software Development", "trainer_id": 2 }
Expected: 201
```

### 5.2 List Batches
```
GET /batches
Auth: Bearer {{token}}
Expected: 200 — array of batches with student_count
```

### 5.3 Add Students to Batch
```
POST /batches/1/students
Auth: Bearer {{token}}
Body: { "student_ids": [3, 4, 5] }
Expected: 200 — { "message": "3 student(s) added to batch" }
```

### 5.4 Get Batch Students
```
GET /batches/1/students
Auth: Bearer {{token}}
Expected: 200 — array of students
```

### 5.5 Remove Student from Batch
```
DELETE /batches/1/students/3
Auth: Bearer {{token}}
Expected: 200
```

### 5.6 Update Batch
```
PUT /batches/1
Auth: Bearer {{token}}
Body: { "trainer_id": 3 }
Expected: 200
```

### 5.7 Delete Batch
```
DELETE /batches/1
Auth: Bearer {{token}}
Expected: 200
```

---

## 6. CLASSES

### 6.1 Schedule Class
```
POST /classes
Auth: Bearer {{token}}
Body: {
  "batch_id": 1,
  "title": "Python Basics — Session 1",
  "class_date": "2026-07-01",
  "start_time": "10:00",
  "end_time": "12:00",
  "location": "Room 201"
}
Expected: 201
```

### 6.2 List Classes
```
GET /classes
Auth: Bearer {{token}}
Expected: 200

GET /classes?batch_id=1
Expected: 200 — only batch 1 classes
```

### 6.3 Delete Class
```
DELETE /classes/1
Auth: Bearer {{token}}
Expected: 200
```

---

## 7. NOTIFICATIONS

### 7.1 Send to All
```
POST /notifications
Auth: Bearer {{token}}
Body: { "title": "Welcome!", "message": "Welcome to PMS 3.0", "target_type": "all" }
Expected: 201
```

### 7.2 Send to Batch
```
POST /notifications
Auth: Bearer {{token}}
Body: { "title": "SD1 Update", "message": "Session tomorrow at 10am", "target_type": "batch", "target_id": 1 }
Expected: 201
```

### 7.3 Send to Student
```
POST /notifications
Auth: Bearer {{token}}
Body: { "title": "Profile Incomplete", "message": "Please complete your profile", "target_type": "student", "target_id": 3 }
Expected: 201
```

### 7.4 Get My Notifications (student)
```
GET /notifications/my
Auth: Bearer {{student_token}}
Expected: 200 — array with is_read field
```

### 7.5 Mark as Read
```
PUT /notifications/1/read
Auth: Bearer {{student_token}}
Expected: 200
```

### 7.6 Delete Notification
```
DELETE /notifications/1
Auth: Bearer {{token}}
Expected: 200
```

---

## 8. STUDENT PROFILES

### 8.1 Get Own Profile (student)
```
GET /students/profile
Auth: Bearer {{student_token}}
Expected: 200 — full profile object
```

### 8.2 Update Own Profile (student)
```
PUT /students/profile
Auth: Bearer {{student_token}}
Body: {
  "gpa": 8.5,
  "phone": "9876543210",
  "skills": "Python, Java, SQL",
  "resume_summary": "Final year CS student at MITADT",
  "linkedin_url": "https://linkedin.com/in/krish",
  "github_url": "https://github.com/krish",
  "education": [{ "degree": "B.Tech CSE", "institution": "MITADT University", "year": "2022-2026", "score": "8.5 CGPA" }],
  "projects": [{ "name": "PMS System", "description": "Placement management", "link": "https://github.com/krish/pms" }]
}
Expected: 200
```

### 8.3 List All Students (trainer/admin)
```
GET /students
Auth: Bearer {{token}}
Expected: 200

GET /students?batch_id=1
GET /students?status=placed
```

### 8.4 Get Student by ID (trainer/admin)
```
GET /students/3
Auth: Bearer {{token}}
Expected: 200 — full profile
```

---

## 9. ATTENDANCE

### 9.1 Record Attendance
```
POST /attendance
Auth: Bearer {{token}}
Body: {
  "student_id": 3,
  "date": "2026-06-20",
  "status": "present",
  "session_name": "Python Basics Session 1",
  "batch_id": 1
}
Expected: 201
```

### 9.2 View All (trainer)
```
GET /attendance
Auth: Bearer {{token}}

GET /attendance?student_id=3
GET /attendance?batch_id=1
```

### 9.3 My Attendance (student)
```
GET /attendance/my
Auth: Bearer {{student_token}}
Expected: 200
```

### 9.4 Delete Record
```
DELETE /attendance/1
Auth: Bearer {{token}}
Expected: 200
```

---

## 10. ASSESSMENTS

### 10.1 Create Assessment
```
POST /assessments
Auth: Bearer {{token}}
Body: {
  "title": "Python Quiz 1",
  "description": "Basics of Python",
  "max_score": 100,
  "date": "2026-06-25",
  "batch_id": 1
}
Expected: 201
```

### 10.2 List Assessments
```
GET /assessments
Auth: Bearer {{token}}
Expected: 200
```

### 10.3 Enter Score
```
POST /assessments/1/scores
Auth: Bearer {{token}}
Body: { "student_id": 3, "score": 85, "feedback": "Good work" }
Expected: 201
```

### 10.4 View Scores
```
GET /assessments/1/scores
Auth: Bearer {{token}}
Expected: 200

GET /assessments/my/scores
Auth: Bearer {{student_token}}
```

---

## 11. PLACEMENT DRIVES

### 11.1 Create Drive
```
POST /drives
Auth: Bearer {{token}}
Body: {
  "company_name": "TCS",
  "job_role": "Software Engineer",
  "package_lpa": 7.5,
  "eligibility_cgpa": 6.5,
  "date": "2026-07-10",
  "status": "upcoming"
}
Expected: 201
```

### 11.2 List Drives
```
GET /drives
Auth: Bearer {{token}}
Expected: 200
```

### 11.3 Apply for Drive (student)
```
POST /drives/1/apply
Auth: Bearer {{student_token}}
Expected: 201
```

### 11.4 My Applications (student)
```
GET /drives/my/applications
Auth: Bearer {{student_token}}
Expected: 200
```

### 11.5 View Drive Applications (trainer)
```
GET /drives/1/applications
Auth: Bearer {{token}}
Expected: 200
```

### 11.6 Update Application Status
```
PUT /drives/applications/1/status?status_val=shortlisted
Auth: Bearer {{token}}
Expected: 200
```

### 11.7 Add Interview Feedback
```
POST /drives/applications/1/feedback
Auth: Bearer {{token}}
Body: {
  "round_name": "Technical Round 1",
  "interviewer_name": "Amit Sharma",
  "rating": 4,
  "comments": "Strong DSA skills"
}
Expected: 201
```

### 11.8 View Interview Feedback
```
GET /drives/applications/1/feedback
Auth: Bearer {{token}}
Expected: 200
```

---

## 12. ANALYTICS

### 12.1 Get Summary
```
GET /analytics
Auth: Bearer {{token}}
Expected: 200 — {
  "total_students": 10,
  "placed_students": 2,
  "placement_percentage": 20.0,
  "average_gpa": 7.8,
  "total_drives": 3,
  "total_colleges": 1,
  "total_batches": 2
}
```

---

## PASSWORD SECURITY NOTE

| Role | Default Password | Example |
|---|---|---|
| Student | Enrollment Number | `CSE2024001` |
| Trainer | Email prefix | `vijay.bhilare` |
| Admin | Set manually at creation | — |

All users have `must_change_password = TRUE` on first login → redirected to set-password page automatically.
