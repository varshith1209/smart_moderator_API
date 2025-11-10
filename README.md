# 🧠 **Smart Content Moderator API**
### *(Django + Django REST Framework + Gemini/OpenAI)*

> ✨ An intelligent moderation service that classifies user-submitted **text** and **images** using **LLMs (Gemini/OpenAI)** or a **local heuristic fallback** — complete with **Slack & Brevo (Sendinblue)** notifications and a simple **analytics API**.

---

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python" /></a>
  <a href="https://www.djangoproject.com/"><img src="https://img.shields.io/badge/Django-5.0-green?logo=django" /></a>
  <a href="https://www.django-rest-framework.org/"><img src="https://img.shields.io/badge/DRF-3.15-red?logo=django" /></a>
  <a href="#"><img src="https://img.shields.io/badge/License-MIT-yellow" /></a>
  <a href="#"><img src="https://img.shields.io/badge/Build-Passing-success" /></a>
</p>

---

## 🚀 **Overview**
This API enables developers to automatically **analyze, classify, and log unsafe content** in user-generated submissions.  
It leverages **LLMs** (like Gemini or OpenAI) and provides **heuristic fallbacks** when offline, ensuring reliability even without API keys.  
Unsafe content triggers **Slack/Email alerts**, and analytics endpoints offer usage insights.

---

## 🧰 **Tech Stack**

| Layer | Technology |
|-------|-------------|
| **Backend** | Django 5, Django REST Framework |
| **Database** | SQLite (default) / PostgreSQL |
| **AI Models** | Gemini (AI Studio) / OpenAI / Stub |
| **Notifications** | Slack Webhooks, Brevo (Sendinblue) |
| **Environment** | Python 3.11+, Virtualenv |

---

## ⚡ **Quickstart**

### 1️⃣ Create a Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
2️⃣ Install Dependencies
```
pip install -r requirements.txt
```
3️⃣ Configure Environment
```
Create a .env file in your project root:

DEBUG=true
DJANGO_SECRET_KEY=dev-secret-key-change-me
ALLOWED_HOSTS=*

# Choose: gemini | openai | stub
LLM_PROVIDER=gemini
OPENAI_API_KEY=
GOOGLE_API_KEY=YOUR_GEMINI_AI_STUDIO_KEY
GEMINI_MODEL=gemini-1.5-pro  # optional fallback

SLACK_WEBHOOK_URL=
BREVO_API_KEY=
BREVO_SENDER_EMAIL=noreply@example.com
BREVO_SENDER_NAME=Moderator
```

4️⃣ Run Migrations
```
python manage.py migrate
```
5️⃣ Start the Server
```
python manage.py runserver
```
🌐 API Endpoints
```
📝 POST /api/v1/moderate/text
```
```
Request:

{
  "email": "user@example.com",
  "text": "some text here"
}

```
```
Response:

{
  "request_id": 1,
  "classification": "safe",
  "confidence": 0.9,
  "reasoning": "Text appears harmless."
}
```

🖼️ POST /api/v1/moderate/image
```
Request (multipart):

email: string

image: file
```
Response: Same as text moderation.
```
```
📊 GET /api/v1/analytics/summary?user=user@example.com
```
```
Response:

{
  "user": "user@example.com",
  "counts": {
    "safe": 10,
    "toxic": 1,
    "harassment": 0,
    "spam": 2
  }
}
```

🧱 Data Model


Model	Fields	Description
ModerationRequest	id, user_email, content_type, content_hash, status, created_at	Tracks moderation requests
ModerationResult	request_id, classification, confidence, reasoning, llm_response	Stores analysis result
NotificationLog	request_id, channel, status, sent_at, details	Tracks alert delivery
💡 Design Choices

✅ Django + DRF → Rapid, maintainable API development
✅ Service Modules → Separation of logic (moderation, LLM, notifications)
✅ Offline Support → Works without API keys via stub mode
✅ Safe Fallbacks → Ensures predictable results on provider errors
✅ Minimal Config → Environment-driven setup for easy deployment

🧪 Testing with cURL
# Moderate text


curl -X POST http://localhost:8000/api/v1/moderate/text ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"user@example.com\",\"text\":\"You are an idiot\"}"

# Moderate image


curl -X POST http://localhost:8000/api/v1/moderate/image ^
  -F "email=user@example.com" ^
  -F "image=@C:/path/to/image.png"

# Analytics summary


curl "http://localhost:8000/api/v1/analytics/summary?user=user@example.com"

🧩 Project Structure

```
moderator/
│
├── api/
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
│
├── moderation/
│   ├── services/
│   │   ├── llm.py
│   │   └── notifications.py
│   ├── models.py
│   └── utils.py
│
├── settings.py
├── manage.py
└── .env
```
🧭 Future Enhancements

 Add Celery + Redis for async moderation

 User dashboards for analytics

 Video & audio moderation support

 Prometheus/Grafana integration for advanced metrics

👨‍💻 Author

[M.varshith ]
📧 varshithmaredoju004.@gmail.com

