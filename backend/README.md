# Student Placement Management System API

A comprehensive FastAPI-based REST API for managing student placements, tracking attendance, assessments, and placement drives in educational institutions.

**LINK**:

## Features

- **User Authentication**: JWT-based authentication with role-based access control (Admin, Trainer, Student)
- **Student Profiles**: Manage student information, GPA, skills, and placement status
- **College Management**: Track multiple colleges and their details
- **Attendance Tracking**: Record and monitor student attendance
- **Assessments**: Create assessments and track student scores with feedback
- **Placement Drives**: Manage company placement drives and student applications
- **Interview Feedback**: Record interview rounds and feedback from interviewers
- **Analytics Dashboard**: View placement statistics and analytics

## Technology Stack

- **Framework**: FastAPI
- **Server**: Uvicorn
- **Database**: PostgreSQL (psycopg2)
- **Authentication**: JWT with python-jose
- **Password Hashing**: Passlib with bcrypt
- **Validation**: Pydantic with email validation
- **CORS**: FastAPI CORS Middleware

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+

### Setup Steps

1. **Clone the repository**
   ```bash
   cd "PMS1.0"
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the project root:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/pms_db
   JWT_SECRET=your_secret_key_here
   JWT_ALGORITHM=HS256
   ```

5. **Run the application**
   ```bash
   uvicorn main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   API documentation: `http://localhost:8000/docs` (Swagger UI)

## Database Structure

The system uses the following tables:
- **users**: User credentials and roles (admin, trainer, student)
- **colleges**: College information and location
- **student_profiles**: Student details linked to users and colleges
- **attendance**: Attendance records with date and status
- **assessments**: Assessment details
- **scores**: Student assessment scores
- **placement_drives**: Company placement drive information
- **applications**: Student applications to placement drives
- **interview_feedback**: Interview feedback for applications

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - Login user
- `GET /me` - Get current user info

### Students
- `GET /students/profile` - Get own student profile
- `PUT /students/profile` - Update student profile

### Colleges
- `POST /colleges` - Create college (Admin)
- `GET /colleges` - List all colleges
- `GET /colleges/{id}` - Get specific college

### Attendance
- `POST /attendance` - Record attendance
- `GET /attendance/student/{id}` - Get student attendance records

### Assessments
- `POST /assessments` - Create assessment (Trainer)
- `GET /assessments` - List assessments
- `POST /assessments/{id}/scores` - Record assessment scores

### Placement Drives
- `POST /drives` - Create placement drive (Admin)
- `GET /drives` - List placement drives
- `POST /drives/{id}/apply` - Apply to placement drive
- `GET /drives/{id}/applications` - View applications

### Analytics
- `GET /analytics/summary` - Get placement statistics

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET` | Secret key for JWT token signing |
| `JWT_ALGORITHM` | Algorithm for JWT encoding (default: HS256) |

## Project Structure

```
PMS1.0/
├── main.py                 # FastAPI application setup
├── auth.py                 # Authentication utilities and JWT handling
├── database.py             # Database connection and initialization
├── schemas.py              # Pydantic models for request/response validation
├── routers/
│   ├── __init__.py
│   ├── auth.py            # Authentication routes
│   ├── colleges.py        # College management routes
│   ├── students.py        # Student profile routes
│   ├── attendance.py      # Attendance tracking routes
│   ├── assessments.py     # Assessment management routes
│   ├── drives.py          # Placement drive routes
│   └── analytics.py       # Analytics routes
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── POSTMAN_TEST_CASES.md  # API test documentation
```

## Authentication & Authorization

The API uses JWT tokens for authentication with the following roles:

- **Admin**: Full access to all resources and management features
- **Trainer**: Can manage assessments and view student progress
- **Student**: Can manage their own profile and view placement opportunities

Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Error Handling

The API returns standard HTTP status codes:
- `200`: Successful request
- `201`: Resource created
- `400`: Bad request
- `401`: Unauthorized (invalid/expired token)
- `403`: Forbidden (insufficient permissions)
- `404`: Resource not found
- `500`: Server error

## Testing

API test cases are documented in [POSTMAN_TEST_CASES.md](POSTMAN_TEST_CASES.md).

Import the test cases into Postman to test all endpoints.

## License

This project is part of the Student Placement Management System.
