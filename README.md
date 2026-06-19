# Placement Management System (PMS 3.0)

A full-stack placement management system for colleges and training institutes.

## Structure

```
├── backend/     → FastAPI + PostgreSQL (deployed on Render)
└── frontend/    → HTML/CSS/JS (deployed on Netlify)
```

## Backend
- **Framework:** FastAPI (Python)
- **Database:** Supabase (PostgreSQL)
- **Deployed at:** https://placement-management-system-u48x.onrender.com
- **Docs:** https://placement-management-system-u48x.onrender.com/docs

## Frontend
- **Stack:** Vanilla HTML, CSS, JavaScript
- **Deployed at:** Netlify (see frontend folder)

## Local Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in your values
uvicorn main:app --reload
```

### Frontend
Open any `.html` file directly in your browser, or use Live Server.
