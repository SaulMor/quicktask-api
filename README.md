![CI](https://github.com/SaulMor/quicktask-api/actions/workflows/ci.yml/badge.svg)

# QuickTask API

A **Scalable To-Do & Notification Backend** built with FastAPI, Async SQLAlchemy, Celery, and Redis, featuring JWT authentication, task CRUD operations, and automated email reminders. Includes a complete CI pipeline with GitHub Actions.

---

## Tech Stack

- **Backend Framework:** FastAPI (async)
- **Database:** SQLite (via SQLAlchemy Async)
- **Background Queue:** Celery with Redis broker & result backend (Docker)
- **Authentication:** JWT (python-jose) + OAuth2 password flow
- **Email Reminders:** Celery tasks scheduling reminder emails (placeholder print)
- **Environment Management:** python-dotenv
- **Testing:** pytest, pytest-asyncio, httpx
- **Lint & Formatting:** flake8, Black, isort
- **CI:** GitHub Actions

---

## Features Implemented

1. **User Management**
   - Register (`POST /auth/register`) with JSON body (`username`, `email`, `password`)
   - Login (`POST /auth/token`) with form data, returns JWT bearer token
   - Protected `GET /users/me`

2. **Task Management**
   - Create Task (`POST /tasks`): `title`, `description`, `deadline`, `reminders` (seconds before)
   - List Tasks (`GET /tasks`)
   - Retrieve Task (`GET /tasks/{task_id}`)
   - Update Task (`PATCH /tasks/{task_id}`)
   - Delete Task (`DELETE /tasks/{task_id}`)

3. **Email Reminders**
   - Tasks accept multiple reminder offsets
   - On creation/update, Celery schedules `send_reminder_email` for each offset
   - Worker (with `--pool=solo` on Windows) processes reminders and prints to console

4. **Persistence & Migrations**
   - SQLAlchemy models: `User` (with `email`), `Task` (stores `reminders` as comma-separated string)
   - `app/init_db.py` to create tables

5. **CI Pipeline**
   - Runs on push & pull_request to `main`
   - Steps:
     1. Checkout code
     2. Setup Python 3.12
     3. Install dependencies (`requirements.txt`)
     4. Initialize DB
     5. Lint with flake8
     6. Format check with Black & isort
     7. Run tests (`pytest`)
   - Status badge in README

---

## Setup & Running Locally

1. **Clone the repo**
   ```bash
   git clone https://github.com/SaulMor/quicktask-api.git
   cd quicktask-api
   ```

2. **Create & activate a virtual environment**
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1  # Windows PowerShell
   # or source venv/bin/activate   # Linux/macOS
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python -m app.init_db
   ```

5. **Start Redis (Docker)**
   ```bash
   docker run -d --name quicktask-redis -p 6379:6379 redis:latest
   ```

6. **Run Celery worker**
   ```bash
   python -m celery -A app.celery_app worker --pool=solo --loglevel=info
   ```

7. **Run the API server**
   ```bash
   uvicorn app.main:app --reload
   ```

8. **Explore**
   - Open Swagger UI: http://127.0.0.1:8000/docs
   - Register, obtain token, authorize, and exercise task endpoints

---

## Testing

```bash
pytest
```

---

## CI/CD

- **GitHub Actions** workflow located at `.github/workflows/ci.yml`
- **Status badge**:
  ```markdown
  ![CI](https://github.com/SaulMor/quicktask-api/actions/workflows/ci.yml/badge.svg)
  ```

---

## Next Steps

- Integrate real email sending (SMTP, AWS SES)
- Add Docker Compose for full stack (API + Redis + worker)
- Deploy to cloud (AWS ECS/Fargate, DigitalOcean)
- Add code coverage reporting (Codecov)
- Implement database migrations (Alembic)
- Improve error handling & logging
