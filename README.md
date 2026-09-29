# Dynamic QR Code Attendance Management System Backend

A modern, secure, and modular REST API backend built with Python 3.12, FastAPI, SQLAlchemy, Alembic, and Pydantic. It provides an attendance tracking system based on dynamically rotating QR codes that refresh every 5 seconds.

## Features

- **JWT Authentication & Authorization**: Secure stateless sessions with role-based access control (`TEACHER` and `STUDENT`).
- **Dynamic QR Code Tokens**:
  - Cryptographically secure random tokens generated server-side.
  - Short-lived validity window of 5 seconds.
  - Server-side time and session validation to prevent tampering.
  - Hashes stored securely to prevent token exposure on database leaks.
  - Auto-upsert to prevent database bloating.
- **Attendance Verification**:
  - Validates session state, token expiration, and time window.
  - Database-level unique constraint to guarantee one student attends a session once.
  - Race-condition handling via transactions.
- **Teacher Dashboard**:
  - Class management (create, view).
  - Attendance session lifecycle (create, start, end).
  - Attendance reports (list, counts, presence/absence stats).
- **Student Dashboard**:
  - Mark attendance by supplying the dynamic QR token.
  - Real-time asynchronous email notifications.
  - Personal attendance history with pagination and class/date filtering.
- **Security Protections**:
  - Rate limiting on Login and Attendance Marking endpoints.
  - Strict security headers (`X-Frame-Options`, `X-Content-Type-Options`, etc.).
  - Proper CORS restrictions.
  - Generic error messages to prevent user/email enumeration.

---

## Tech Stack

- **Framework**: FastAPI (Python 3.12+)
- **ORM**: SQLAlchemy 2.0 (Async mode)
- **Database**: SQLite (via aiosqlite)
- **Migrations**: Alembic
- **Validation**: Pydantic v2 & Pydantic Settings v2
- **Auth**: PyJWT (python-jose), Passlib (Bcrypt)
- **Rate Limiting**: Slowapi (Limits)
- **Email**: aiosmtplib (SMTP)
- **Testing**: Pytest & Httpx (Async testing)

---

## Project Structure

```text
dynamic-qr-attendance/
│
├── app/
│   ├── main.py                 # Application entrypoint & middlewares
│   ├── core/
│   │   ├── config.py           # Configuration & Settings (Pydantic)
│   │   ├── database.py         # Async DB engine & Session setup
│   │   ├── security.py         # Hashing & Token generation utils
│   │   └── exceptions.py       # Custom HTTP exceptions
│   ├── models/
│   │   └── models.py           # SQLAlchemy database schemas
│   ├── schemas/
│   │   └── schemas.py          # Pydantic validation schemas
│   ├── routers/
│   │   ├── auth_router.py      # Registration, Login, Profile
│   │   ├── class_router.py     # Class management endpoints
│   │   ├── session_router.py   # Attendance session controls & QR token generation
│   │   ├── attendance_router.py# Student marking & history retrieval
│   │   └── teacher_router.py   # Session rosters & stats
│   ├── services/
│   │   ├── auth_service.py     # Authentication logic
│   │   ├── class_service.py    # Class CRUD logic
│   │   ├── session_service.py  # Session state & duration logic
│   │   ├── qr_service.py       # Cryptographic token management
│   │   ├── attendance_service.py# Validation chain & DB commit logic
│   │   └── email_service.py    # SMTP & Mock/Console email service
│   ├── dependencies/
│   │   └── auth.py             # FastAPI dependency injectables
│   └── utils/
│
├── tests/                      # Pytest Async unit & integration tests
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_sessions.py
│   ├── test_qr.py
│   └── test_attendance.py
│
├── alembic/                    # Database migrations
│   ├── env.py
│   └── versions/
│
├── .env.example                # Template environmental config
├── .env                        # Local development variables
├── .gitignore
├── requirements.txt            # Dependency configuration
└── README.md
```

---

## Setup Instructions

### 1. Clone & Navigate to Repository
Ensure you are in the project folder:
```bash
cd dynamic-qr-attendance
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
py -3.12 -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration
Create a `.env` file from the example:
```bash
copy .env.example .env
```
Update parameters such as `JWT_SECRET_KEY` and SMTP settings as desired. If `SMTP_HOST` is left empty, the application falls back to logging emails to the console for easy debugging.

### 5. Running Migrations
Apply Alembic migrations to setup the database tables:
```bash
alembic upgrade head
```

### 6. Run the Application
Start the development server:
```bash
uvicorn app.main:app --reload
```
Access the Swagger interactive API documentation at: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**.

---

## Testing

Run the test suite using pytest:
```bash
pytest -v
```
All tests use an in-memory SQLite database to ensure total isolation and fast execution.
