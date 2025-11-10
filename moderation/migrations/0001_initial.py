from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
	initial = True

	dependencies = []

	operations = [
		migrations.CreateModel(
			name="ModerationRequest",
			fields=[
				("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
				("user_email", models.EmailField(db_index=True, max_length=254)),
				("content_type", models.CharField(choices=[("text", "Text"), ("image", "Image")], max_length=16)),
				("content_hash", models.CharField(db_index=True, max_length=128)),
				("status", models.CharField(choices=[("pending", "Pending"), ("completed", "Completed"), ("failed", "Failed")], default="pending", max_length=16)),
				("created_at", models.DateTimeField(auto_now_add=True)),
			],
		),
		migrations.CreateModel(
			name="ModerationResult",
			fields=[
				("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
				("classification", models.CharField(max_length=32)),
				("confidence", models.FloatField()),
				("reasoning", models.TextField(blank=True)),
				("llm_response", models.JSONField()),
				("request", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="result", to="moderation.moderationrequest")),
			],
		),
		migrations.CreateModel(
			name="NotificationLog",
			fields=[
				("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
				("channel", models.CharField(choices=[("slack", "Slack"), ("email", "Email")], max_length=16)),
				("status", models.CharField(max_length=16)),
				("sent_at", models.DateTimeField(auto_now_add=True)),
				("details", models.TextField(blank=True)),
				("request", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="moderation.moderationrequest")),
			],
		),
	]


