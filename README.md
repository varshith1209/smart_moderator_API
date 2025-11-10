## Smart Content Moderator API (Django + DRF)

A simple content moderation service that classifies user-submitted text/images using an LLM (OpenAI/Gemini or a local heuristic fallback), stores results, sends Slack/Brevo email alerts for unsafe content, and exposes analytics.

### Tech
- Django 5 + Django REST Framework
- SQLite (default)
- Gemini for LLM (AI Studio key), Slack webhook, Brevo (Sendinblue) for email

### Quickstart
1. Create and activate a virtual environment (Windows PowerShell):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Environment variables:
   Create a `.env` file in the repository root:
   ```
   DEBUG=true
   DJANGO_SECRET_KEY=dev-secret-key-change-me
   ALLOWED_HOSTS=*
   # Choose provider: gemini | openai | stub
   LLM_PROVIDER=gemini
   OPENAI_API_KEY=
   GOOGLE_API_KEY=YOUR_GEMINI_AI_STUDIO_KEY
   GEMINI_MODEL=gemini-1.5-pro  # optional; client tries common pro fallbacks
   SLACK_WEBHOOK_URL=
   BREVO_API_KEY=
   BREVO_SENDER_EMAIL=noreply@example.com
   BREVO_SENDER_NAME=Moderator
   ```
   - Leave `LLM_PROVIDER=stub` for offline heuristic moderation.
   - Set Slack/Brevo keys to enable notifications.
4. Initialize DB:
   ```powershell
   python manage.py migrate
   ```
5. Run server:
   ```powershell
   python manage.py runserver
   ```

### API
- POST `/api/v1/moderate/text`
  - Body (JSON):
    ```json
    { "email": "user@example.com", "text": "some text here" }
    ```
  - Response:
    ```json
    { "request_id": 1, "classification": "safe", "confidence": 0.9, "reasoning": "..." }
    ```
- POST `/api/v1/moderate/image`
  - Multipart form-data:
    - `email`: string
    - `image`: file
  - Response same shape as text.
- GET `/api/v1/analytics/summary?user=user@example.com`
  - Response:
    ```json
    { "user": "user@example.com", "counts": { "safe": 10, "toxic": 1, "harassment": 0, "spam": 2 } }
    ```

### Data Model
- `ModerationRequest(id, user_email, content_type[text|image], content_hash, status[pending|completed|failed], created_at)`
- `ModerationResult(request_id[1:1], classification, confidence, reasoning, llm_response[JSON])`
- `NotificationLog(request_id, channel[slack|email], status[sent|failed], sent_at, details)`

### Notes & Assumptions
- Async processing is intentionally skipped (per assignment) and handled inline.
- Provider selection via `LLM_PROVIDER` (gemini | openai | stub). If keys are missing, a deterministic heuristic is used.
- On provider/API errors, responses return a generic `reasoning`: "Provider error: unable to load model. Falling back to safe heuristic." (no URLs or internal details are exposed).
- Notifications are attempted only for results where `classification != "safe"`.
- SQLite is the default DB; swap to PostgreSQL by editing `DATABASES` in `moderator/settings.py`.

### Testing with curl
```bash
curl -X POST http://localhost:8000/api/v1/moderate/text ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"user@example.com\",\"text\":\"You are an idiot\"}"
```

```bash
curl -X POST http://localhost:8000/api/v1/moderate/image ^
  -F "email=user@example.com" ^
  -F "image=@C:/path/to/image.png"
```

```bash
curl "http://localhost:8000/api/v1/analytics/summary?user=user@example.com"
```

### Why these choices?
- Django + DRF for fast, structured API development with strong ORM and migrations.
- Service modules (`moderation/services/*`) separate LLM and notification concerns from views.
- Heuristic fallback keeps the app functional without external credentials; simple to switch providers via env.


