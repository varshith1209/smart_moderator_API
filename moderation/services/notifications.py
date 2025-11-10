from typing import Optional
import requests
from django.conf import settings


def send_slack_message(text: str) -> tuple[bool, str]:
	webhook = settings.SLACK_WEBHOOK_URL
	if not webhook:
		return False, "SLACK_WEBHOOK_URL not set"
	try:
		resp = requests.post(webhook, json={"text": text}, timeout=10)
		if resp.ok:
			return True, "sent"
		return False, f"slack_error:{resp.status_code} {resp.text}"
	except Exception as e:
		return False, f"slack_exception:{e}"


def send_email_brevo(to_email: str, subject: str, html_content: str) -> tuple[bool, str]:
	api_key = settings.BREVO_API_KEY
	if not api_key:
		return False, "BREVO_API_KEY not set"
	try:
		url = "https://api.brevo.com/v3/smtp/email"
		headers = {
			"accept": "application/json",
			"content-type": "application/json",
			"api-key": api_key,
		}
		payload = {
			"sender": {"name": settings.BREVO_SENDER_NAME, "email": settings.BREVO_SENDER_EMAIL},
			"to": [{"email": to_email}],
			"subject": subject,
			"htmlContent": html_content,
		}
		resp = requests.post(url, json=payload, headers=headers, timeout=15)
		if resp.ok:
			return True, "sent"
		return False, f"brevo_error:{resp.status_code} {resp.text}"
	except Exception as e:
		return False, f"brevo_exception:{e}"


