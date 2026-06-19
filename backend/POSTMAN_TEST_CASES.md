# PMS1.0 API Test Cases for Postman

Base URL: `http://127.0.0.1:8000`

## Common Notes
- Use `Content-Type: application/json` for all JSON requests.
- For protected endpoints, add header:
  - `Authorization: Bearer <token>`
- Use `/login` response token for subsequent requests.
- `POST /register` returns user `id`, `email`, and `role`.
- Use separate accounts for each role: admin, trainer, student.

---

## Authentication Tests (All Roles)

### 1. Register Admin
- Method: `POST`
- URL: `/register`
- Body:
```json
{
  "email": "admin@example.com",
  "password": "Admin123!",
  "role": "admin"
}
```
- Expected: `201 Created`, user object with `role: "admin"`

### 2. Register Trainer
- Method: `POST`
- URL: `/register`
- Body:
```json
{
  "email": "trainer@example.com",
  "password": "Trainer123!",
  "role": "trainer"
}
```

### 3. Register Student
- Method: `POST`
- URL: `/register`
- Body:
```json
{
  "email": "student@example.com",
  "password": "Student123!",
  "role": "student"
}
```

### 4. Login User
- Method: `POST`
- URL: `/login`
- Body:
```json
{
  "email": "student@example.com",
  "password": "Student123!"
}
```
- Expected: JSON with `token` and `token_type`

### 5. Get Current User
- Method: `GET`
- URL: `/me`
- Header: `Authorization: Bearer <token>`
- Expected: current user object

---

## Admin Test Cases

Admin can perform all admin tasks and can also access trainer-level routes because `require_trainer` permits admin users.

### A1. Create Placement Drive
- Method: `POST`
- URL: `/drives`
- Header: `Authorization: Bearer <admin-token>`
- Body:
```json
{
  "company_name": "TestCorp",
  "job_role": "Intern",
  "package_lpa": 5.5,
  "eligibility_cgpa": 7.0,
  "date": "2026-08-01",
  "status": "active"
}
```

### A2. List All Placement Drives
- Method: `GET`
- URL: `/drives`
- Header: `Authorization: Bearer <admin-token>`

### A3. View Drive Applications
- Method: `GET`
- URL: `/drives/{drive_id}/applications`
- Header: `Authorization: Bearer <admin-token>`

### A4. View Analytics
- Method: `GET`
- URL: `/analytics`
- Header: `Authorization: Bearer <admin-token>`

### A5. (Optional) Use Trainer-level Routes
- Admin can also test trainer routes such as `/attendance`, `/assessments`, `/drives/applications/{id}/status`, and `/drives/applications/{id}/feedback`.

---

## Trainer Test Cases

Trainer has permission to manage attendance, assessments, application workflows, and feedback.

### T1. Record Attendance
- Method: `POST`
- URL: `/attendance`
- Header: `Authorization: Bearer <trainer-token>`
- Body:
```json
{
  "student_id": 3,
  "date": "2026-06-17",
  "status": "present",
  "session_name": "Intro Session"
}
```

### T2. List Attendance Records
- Method: `GET`
- URL: `/attendance`
- Header: `Authorization: Bearer <trainer-token>`
- Optional Query: `student_id=3`

### T3. Create Assessment
- Method: `POST`
- URL: `/assessments`
- Header: `Authorization: Bearer <trainer-token>`
- Body:
```json
{
  "title": "Midterm",
  "description": "Midterm Assessment",
  "max_score": 100,
  "date": "2026-07-01"
}
```

### T4. Enter Student Score
- Method: `POST`
- URL: `/assessments/{assessment_id}/scores`
- Header: `Authorization: Bearer <trainer-token>`
- Body:
```json
{
  "student_id": 3,
  "score": 92,
  "feedback": "Great work"
}
```

### T5. List Assessment Scores
- Method: `GET`
- URL: `/assessments/{assessment_id}/scores`
- Header: `Authorization: Bearer <trainer-token>`

### T6. View Placement Drive Applications
- Method: `GET`
- URL: `/drives/{drive_id}/applications`
- Header: `Authorization: Bearer <trainer-token>`

### T7. Update Application Status
- Method: `PUT`
- URL: `/drives/applications/{application_id}/status?status_val=selected`
- Header: `Authorization: Bearer <trainer-token>`

### T8. Leave Interview Feedback
- Method: `POST`
- URL: `/drives/applications/{application_id}/feedback`
- Header: `Authorization: Bearer <trainer-token>`
- Body:
```json
{
  "round_name": "Round 1",
  "interviewer_name": "HR",
  "rating": 5,
  "comments": "Excellent"
}
```

### T9. View Application Feedback
- Method: `GET`
- URL: `/drives/applications/{application_id}/feedback`
- Header: `Authorization: Bearer <trainer-token>`

---

## Student Test Cases

Student can update their own profile, view attendance, assessments, apply to drives, and view feedback.

### S1. Update Student Profile
- Method: `PUT`
- URL: `/students/profile`
- Header: `Authorization: Bearer <student-token>`
- Body:
```json
{
  "roll_number": "S101",
  "college_id": 1,
  "branch": "CSE",
  "gpa": 8.5,
  "resume_url": "https://resume.example.com",
  "skills": "Python, SQL",
  "status": "unplaced"
}
```

### S2. Get Own Profile
- Method: `GET`
- URL: `/students/profile`
- Header: `Authorization: Bearer <student-token>`

### S3. View My Attendance
- Method: `GET`
- URL: `/attendance/my`
- Header: `Authorization: Bearer <student-token>`

### S4. List Assessments
- Method: `GET`
- URL: `/assessments`
- Header: `Authorization: Bearer <student-token>`

### S5. View My Assessment Scores
- Method: `GET`
- URL: `/assessments/my/scores`
- Header: `Authorization: Bearer <student-token>`

### S6. Apply for Placement Drive
- Method: `POST`
- URL: `/drives/{drive_id}/apply`
- Header: `Authorization: Bearer <student-token>`

### S7. View My Applications
- Method: `GET`
- URL: `/drives/my/applications`
- Header: `Authorization: Bearer <student-token>`

### S8. View Drive Application Results
- Method: `GET`
- URL: `/drives/{drive_id}/applications`
- Header: `Authorization: Bearer <student-token>`

### S9. View Interview Feedback
- Method: `GET`
- URL: `/drives/applications/{application_id}/feedback`
- Header: `Authorization: Bearer <student-token>`

---

## Endpoint Summary Table

| Role | Endpoint | Method | Purpose |
|------|----------|--------|---------|
| All | `/register` | POST | Create user account |
| All | `/login` | POST | Authenticate and receive JWT |
| All | `/me` | GET | Get current logged-in user |
| All | `/colleges` | GET | List colleges |
| Student | `/students/profile` | GET | Get student own profile |
| Student | `/students/profile` | PUT | Update student profile |
| Trainer/Admin | `/attendance` | POST | Record attendance |
| Trainer/Admin | `/attendance` | GET | List attendance |
| Student | `/attendance/my` | GET | Get own attendance |
| Trainer/Admin | `/assessments` | POST | Create assessment |
| Any | `/assessments` | GET | List assessments |
| Trainer/Admin | `/assessments/{id}/scores` | POST | Add/update score |
| Trainer/Admin | `/assessments/{id}/scores` | GET | List assessment scores |
| Student | `/assessments/my/scores` | GET | View own scores |
| Admin | `/drives` | POST | Create placement drive |
| Any | `/drives` | GET | List drives |
| Student | `/drives/{id}/apply` | POST | Apply to a drive |
| Student | `/drives/my/applications` | GET | View own applications |
| Any | `/drives/{id}/applications` | GET | View applications for a drive |
| Trainer/Admin | `/drives/applications/{id}/status` | PUT | Update application status |
| Trainer/Admin | `/drives/applications/{id}/feedback` | POST | Add interview feedback |
| Any | `/drives/applications/{id}/feedback` | GET | View feedback |
| Trainer/Admin | `/analytics` | GET | Get placement analytics |

---

## Postman Setup Steps
1. Create a new Postman Collection.
2. Create an environment with variable `baseUrl = http://127.0.0.1:8000`.
3. Use `{{baseUrl}}` for the request URL.
4. Add `Authorization` header only after login.
5. Use the `token` from `POST /login` as `Bearer <token>`.
6. Create separate admin, trainer, and student accounts.

---

## Tips
- If a route returns `405 Method Not Allowed`, confirm the HTTP method and route path.
- If a route returns `401 Unauthorized`, ensure `Authorization: Bearer <token>` is set correctly.
- For trainer endpoints, use the registered student `id` from `POST /register`.
- For `PUT /drives/applications/{application_id}/status`, use query param `status_val=selected|shortlisted|rejected|applied`.
