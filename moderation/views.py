from typing import Dict
from django.db import transaction
from django.utils import timezone
from rest_framework import status, views
from rest_framework.response import Response

from .models import ModerationRequest, ModerationResult, NotificationLog
from .serializers import (
	TextModerationRequestSerializer,
	ImageModerationRequestSerializer,
	ModerationResultSerializer,
)
from .utils import sha256_text, sha256_bytes
from .services.llm_client import classify_text, classify_image
from .services.notifications import send_slack_message, send_email_brevo


class ModerateTextView(views.APIView):
	def post(self, request):
		serializer = TextModerationRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		email = serializer.validated_data["email"]
		text = serializer.validated_data["text"]

		content_hash = sha256_text(text)

		with transaction.atomic():
			req = ModerationRequest.objects.create(
				user_email=email,
				content_type=ModerationRequest.ContentType.TEXT,
				content_hash=content_hash,
				status=ModerationRequest.Status.PENDING,
			)
			try:
				label, conf, reason, raw = classify_text(email=email, text=text)
				res = ModerationResult.objects.create(
					request=req,
					classification=label,
					confidence=conf,
					reasoning=reason,
					llm_response=raw,
				)
				req.status = ModerationRequest.Status.COMPLETED
				req.save(update_fields=["status"])
			finally:
				pass

		# If inappropriate, notify via Slack/Email
		if label != "safe":
			msg = f"[Content Alert] {email} submitted {label} content (conf {conf:.2f}). Request #{req.id}"
			ok, details = send_slack_message(msg)
			NotificationLog.objects.create(
				request=req,
				channel=NotificationLog.Channel.SLACK,
				status="sent" if ok else "failed",
				details=details,
			)
			ok_e, details_e = send_email_brevo(
				to_email=email,
				subject=f"Content Moderation Alert: {label}",
				html_content=f"<p>Your recent submission was flagged: <b>{label}</b> (confidence {conf:.2f}).</p>",
			)
			NotificationLog.objects.create(
				request=req,
				channel=NotificationLog.Channel.EMAIL,
				status="sent" if ok_e else "failed",
				details=details_e,
			)

		out = ModerationResultSerializer(
			{
				"request_id": req.id,
				"classification": label,
				"confidence": conf,
				"reasoning": reason,
			}
		).data
		return Response(out, status=status.HTTP_200_OK)


class ModerateImageView(views.APIView):
	def post(self, request):
		serializer = ImageModerationRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		email = serializer.validated_data["email"]
		image = serializer.validated_data["image"]
		image_bytes = image.read()

		content_hash = sha256_bytes(image_bytes)

		with transaction.atomic():
			req = ModerationRequest.objects.create(
				user_email=email,
				content_type=ModerationRequest.ContentType.IMAGE,
				content_hash=content_hash,
				status=ModerationRequest.Status.PENDING,
			)
			try:
				label, conf, reason, raw = classify_image(email=email, image_bytes=image_bytes)
				res = ModerationResult.objects.create(
					request=req,
					classification=label,
					confidence=conf,
					reasoning=reason,
					llm_response=raw,
				)
				req.status = ModerationRequest.Status.COMPLETED
				req.save(update_fields=["status"])
			finally:
				pass

		if label != "safe":
			msg = f"[Image Alert] {email} submitted {label} image (conf {conf:.2f}). Request #{req.id}"
			ok, details = send_slack_message(msg)
			NotificationLog.objects.create(
				request=req,
				channel=NotificationLog.Channel.SLACK,
				status="sent" if ok else "failed",
				details=details,
			)
			ok_e, details_e = send_email_brevo(
				to_email=email,
				subject=f"Image Moderation Alert: {label}",
				html_content=f"<p>Your recent image was flagged: <b>{label}</b> (confidence {conf:.2f}).</p>",
			)
			NotificationLog.objects.create(
				request=req,
				channel=NotificationLog.Channel.EMAIL,
				status="sent" if ok_e else "failed",
				details=details_e,
			)

		out = ModerationResultSerializer(
			{
				"request_id": req.id,
				"classification": label,
				"confidence": conf,
				"reasoning": reason,
			}
		).data
		return Response(out, status=status.HTTP_200_OK)


class AnalyticsSummaryView(views.APIView):
	def get(self, request):
		email = request.query_params.get("user")
		if not email:
			return Response({"detail": "Missing user query parameter"}, status=status.HTTP_400_BAD_REQUEST)

		qs = ModerationResult.objects.filter(request__user_email=email).values_list("classification", flat=True)
		counts: Dict[str, int] = {"safe": 0, "toxic": 0, "harassment": 0, "spam": 0}
		for c in qs:
			counts[c] = counts.get(c, 0) + 1
		return Response({"user": email, "counts": counts}, status=status.HTTP_200_OK)


