import base64
from typing import Any, Dict, Tuple
import requests
from django.conf import settings

Classification = Tuple[str, float, str, Dict[str, Any]]


def _heuristic_label_from_text(text: str) -> Tuple[str, float, str]:
	lower = text.lower()
	if any(w in lower for w in ["buy now", "free money", "click here"]):
		return "spam", 0.85, "Detected common spam phrases."
	if any(w in lower for w in ["idiot", "stupid", "hate you"]):
		return "harassment", 0.80, "Detected abusive language."
	if any(w in lower for w in ["kill", "die", "bomb"]):
		return "toxic", 0.75, "Detected highly toxic terms."
	return "safe", 0.9, "No unsafe indicators found."


def classify_text(email: str, text: str) -> Classification:
	"""Classify text content using selected provider; falls back to heuristic with generic reasoning."""
	provider = (getattr(settings, "LLM_PROVIDER", "gemini") or "gemini").lower()

	# ---------------- OPENAI ----------------
	if provider == "openai" and getattr(settings, "OPENAI_API_KEY", None):
		try:
			url = "https://api.openai.com/v1/chat/completions"
			headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
			system = (
				"You are a content moderation classifier. Reply with JSON: "
				"{classification: one of [toxic, spam, harassment, safe], confidence: 0..1, reasoning: short}."
			)
			user = f"Classify the following text for policy compliance:\n\n{text}"
			payload = {
				"model": "gpt-4o-mini",
				"messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
				"temperature": 0.0,
			}
			resp = requests.post(url, json=payload, headers=headers, timeout=20)
			resp.raise_for_status()
			data = resp.json()
			content = data["choices"][0]["message"]["content"]
			import json
			start = content.find("{")
			end = content.rfind("}") + 1
			obj = json.loads(content[start:end]) if start != -1 and end != -1 else {}
			classification = obj.get("classification", "safe").lower()
			confidence = float(obj.get("confidence", 0.7))
			reasoning = obj.get("reasoning", "")
			return classification, confidence, reasoning, data
		except Exception:
			label, conf, _ = _heuristic_label_from_text(text)
			return label, conf, "Provider error: unable to load model. Falling back to safe heuristic.", {"error": "openai_error"}

	# ---------------- GEMINI ----------------
	if provider == "gemini" and getattr(settings, "GOOGLE_API_KEY", None):
		try:
			# Prefer Pro variants; ignore env unless it is a Pro variant. Use v1beta only.
			env_model = getattr(settings, "GEMINI_MODEL", "gemini-1.5-pro") or "gemini-1.5-pro"
			allowed_pro = {"gemini-1.5-pro", "gemini-1.5-pro-latest", "gemini-pro"}
			models = [env_model] if env_model in allowed_pro else []
			models += ["gemini-1.5-pro", "gemini-1.5-pro-latest", "gemini-pro"]
			versions = ["v1beta"]
			prompt = (
				"You are a content moderation classifier. Reply with JSON only: "
				"{classification: one of [toxic, spam, harassment, safe], confidence: 0..1, reasoning: short}.\n\n"
				f"Text:\n{text}"
			)
			payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.0, "maxOutputTokens": 512}}
			last_error = None
			for ver in versions:
				for model in models:
					url = f"https://generativelanguage.googleapis.com/{ver}/models/{model}:generateContent?key={settings.GOOGLE_API_KEY}"
					try:
						resp = requests.post(
							url,
							json=payload,
							headers={"Content-Type": "application/json"},
							timeout=20,
						)
						resp.raise_for_status()
						data = resp.json()
						# Extract text from Gemini response
						candidates = data.get("candidates") or []
						if not candidates:
							raise ValueError("No candidates in Gemini response")
						parts = ((candidates[0] or {}).get("content") or {}).get("parts") or []
						if not parts:
							raise ValueError("No parts in Gemini response")
						cand_text = parts[0].get("text", "")
						import json
						start = cand_text.find("{")
						end = cand_text.rfind("}") + 1
						obj = json.loads(cand_text[start:end]) if start != -1 and end != -1 else {}
						classification = obj.get("classification", "safe").lower()
						confidence = float(obj.get("confidence", 0.7))
						reasoning = obj.get("reasoning", "")
						return classification, confidence, reasoning, data
					except Exception as inner_e:
						last_error = inner_e
						continue
			# If all attempts failed:
			raise last_error or RuntimeError("Gemini request failed")
		except Exception:
			label, conf, _ = _heuristic_label_from_text(text)
			return label, conf, "Provider error: unable to load model. Falling back to safe heuristic.", {"error": "gemini_error"}

	# Fallback when no key
	label, conf, why = _heuristic_label_from_text(text)
	return label, conf, why, {"provider": "stub"}


def classify_image(email: str, image_bytes: bytes) -> Classification:
	"""Classify image content using selected provider; falls back to heuristic with generic reasoning."""
	provider = (getattr(settings, "LLM_PROVIDER", "gemini") or "gemini").lower()

	# Note: OpenAI path omitted for image to keep code minimal; can be added similarly if needed.
	if provider == "gemini" and getattr(settings, "GOOGLE_API_KEY", None):
		try:
			env_model = getattr(settings, "GEMINI_MODEL", "gemini-1.5-pro") or "gemini-1.5-pro"
			allowed_pro = {"gemini-1.5-pro", "gemini-1.5-pro-latest", "gemini-pro"}
			models = [env_model] if env_model in allowed_pro else []
			models += ["gemini-1.5-pro", "gemini-1.5-pro-latest", "gemini-pro"]
			versions = ["v1beta"]
			encoded = base64.b64encode(image_bytes).decode("utf-8")
			instruction = (
				"You are an image content moderation classifier. Reply with JSON only: "
				"{classification: one of [toxic, spam, harassment, safe], confidence: 0..1, reasoning: short}."
			)
			last_error = None
			for ver in versions:
				for model in models:
					url = f"https://generativelanguage.googleapis.com/{ver}/models/{model}:generateContent?key={settings.GOOGLE_API_KEY}"
					payload = {
						"contents": [
							{
								"parts": [
									{"text": instruction},
									{"inline_data": {"mime_type": "image/png", "data": encoded}},
								]
							}
						]
					}
					try:
						resp = requests.post(
							url,
							json=payload,
							headers={"Content-Type": "application/json"},
							timeout=30,
						)
						resp.raise_for_status()
						data = resp.json()
						candidates = data.get("candidates") or []
						if not candidates:
							raise ValueError("No candidates in Gemini response")
						parts = ((candidates[0] or {}).get("content") or {}).get("parts") or []
						if not parts:
							raise ValueError("No parts in Gemini response")
						cand_text = parts[0].get("text", "")
						import json
						start = cand_text.find("{")
						end = cand_text.rfind("}") + 1
						obj = json.loads(cand_text[start:end]) if start != -1 and end != -1 else {}
						classification = obj.get("classification", "safe").lower()
						confidence = float(obj.get("confidence", 0.7))
						reasoning = obj.get("reasoning", "")
						return classification, confidence, reasoning, data
					except Exception as inner_e:
						last_error = inner_e
						continue
			raise last_error or RuntimeError("Gemini image request failed")
		except Exception:
			return "safe", 0.7, "Provider error: unable to load model. Falling back to safe heuristic.", {"error": "gemini_error"}
	return "safe", 0.8, "No unsafe indicators found (stub).", {"provider": "stub"}
