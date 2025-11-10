from django.db import models


class ModerationRequest(models.Model):
	class ContentType(models.TextChoices):
		TEXT = "text", "Text"
		IMAGE = "image", "Image"

	class Status(models.TextChoices):
		PENDING = "pending", "Pending"
		COMPLETED = "completed", "Completed"
		FAILED = "failed", "Failed"

	user_email = models.EmailField(db_index=True)
	content_type = models.CharField(max_length=16, choices=ContentType.choices)
	content_hash = models.CharField(max_length=128, db_index=True)
	status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return f"{self.user_email} · {self.content_type} · {self.status}"


class ModerationResult(models.Model):
	request = models.OneToOneField(ModerationRequest, on_delete=models.CASCADE, related_name="result")
	classification = models.CharField(max_length=32)  # toxic, spam, harassment, safe
	confidence = models.FloatField()
	reasoning = models.TextField(blank=True)
	llm_response = models.JSONField()

	def __str__(self) -> str:
		return f"{self.request_id} · {self.classification} ({self.confidence:.2f})"


class NotificationLog(models.Model):
	class Channel(models.TextChoices):
		SLACK = "slack", "Slack"
		EMAIL = "email", "Email"

	request = models.ForeignKey(ModerationRequest, on_delete=models.CASCADE, related_name="notifications")
	channel = models.CharField(max_length=16, choices=Channel.choices)
	status = models.CharField(max_length=16)  # sent, failed
	sent_at = models.DateTimeField(auto_now_add=True)
	details = models.TextField(blank=True)

	def __str__(self) -> str:
		return f"{self.request_id} · {self.channel} · {self.status}"


