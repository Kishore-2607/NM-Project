# FitBuddy – AI Fitness Plan Generator

FitBuddy is a FastAPI web application that generates personalized 7-day workout plans and nutrition/recovery tips, then revises the plan from user feedback.

## Features

- FastAPI backend
- Jinja2 HTML frontend
- SQLite + SQLAlchemy persistence
- Google Gemini integration through the current `google-genai` SDK
- 7-day workout generation
- Nutrition/recovery tip generation
- Feedback-based plan regeneration
- Admin/coach dashboard
- JSON API endpoints
- Pydantic validation
- Local mock-AI mode for UI/testing without an API key
- Automated pytest tests
- Swagger/OpenAPI docs at `/docs`

## Project structure

```text
FitBuddy/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── schemas.py
│   ├── ai_service.py
│   ├── gemini_generator.py
│   ├── gemini_flash_generator.py
│   ├── updated_plan.py
│   ├── routes.py
│   ├── templates/
│   │   ├── index.html
│   │   ├── result.html
│   │   ├── all_users.html
│   │   └── error.html
│   └── static/
│       └── css/
│           └── style.css
├── tests/
│   ├── __init__.py
│   └── test_app.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## VS Code setup – Windows

1. Install Python 3.11 or newer.
2. Open this `FitBuddy` folder in VS Code.
3. Open **Terminal → New Terminal**.
4. Create a virtual environment:

```powershell
python -m venv .venv
```

5. Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```cmd
.venv\Scripts\activate
```

6. Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

7. Copy `.env.example` to `.env`.

For a no-key local demo, set:

```env
MOCK_AI=true
```

For real Gemini generation, set:

```env
GEMINI_API_KEY=your_key_here
MOCK_AI=false
```

8. Start the server:

```powershell
uvicorn app.main:app --reload
```

9. Open:

- Web app: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health
- Admin dashboard: http://127.0.0.1:8000/view-all-users

## Testing

Run:

```powershell
pytest -q
```

The tests use `MOCK_AI=true`, so they do not consume Gemini API calls.

## API examples

### Generate a plan

```http
POST /api/generate-workout
Content-Type: application/json
```

```json
{
  "name": "Kishore",
  "user_id": "kishore01",
  "age": 22,
  "weight": 70,
  "goal": "muscle gain",
  "intensity": "medium"
}
```

### Update a plan

```http
POST /api/submit-feedback
Content-Type: application/json
```

```json
{
  "user_id": "kishore01",
  "feedback": "Add more cardio and include an extra recovery day."
}
```

### List users

```http
GET /api/users
```

## Gemini configuration

The original project documentation names Gemini 1.5 Pro and Gemini Flash. Those model names are historical. This implementation uses the current Google GenAI SDK and configurable model IDs instead of hard-coding the legacy SDK.

Default configuration:

```env
GEMINI_PLAN_MODEL=gemini-3.8-flash
GEMINI_TIP_MODEL=gemini-3.8-flash
```

If your Google AI Studio/API project does not have access to a configured model, change the corresponding `.env` value to a model available to your project.

## Database

SQLite is created automatically as:

```text
fitbuddy.db
```

It contains:

- `users`
- `plans`

The original and updated plans are kept separately.

## Admin protection

For a local demo, `/view-all-users` is open by default.

To enable a simple shared-key gate:

```env
ADMIN_KEY=change-this-value
```

Then open:

```text
http://127.0.0.1:8000/view-all-users?admin_key=change-this-value
```

For production, replace this with proper authentication/authorization.

## Important health note

FitBuddy is a general wellness application. AI-generated exercise and nutrition content can be incorrect or inappropriate for an individual. The UI therefore avoids presenting the output as medical advice. Users with injuries, medical conditions, pregnancy-related considerations, or other special circumstances should consult a qualified professional before following a new exercise or diet program.

## Production hardening

Before public deployment:

- Add real authentication and role-based authorization.
- Protect admin APIs and deletion endpoints.
- Add CSRF protection for browser forms.
- Add database migrations (Alembic).
- Add rate limiting and request logging.
- Store secrets in a managed secret store.
- Add structured AI output validation.
- Add a production database such as PostgreSQL.
- Add monitoring and error tracking.
