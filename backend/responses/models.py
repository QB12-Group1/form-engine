from django.db import models


class ResponseSession(models.Model):
    survey = models.ForeignKey(
        "surveys.Survey", on_delete=models.CASCADE, related_name="response_session"
    )
    respondent_ip = models.CharField(max_length=50)
    user_agent = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session #{self.pk}"


class Answer(models.Model):
    question = models.ForeignKey(
        "surveys.Question", on_delete=models.CASCADE, related_name="answers"
    )
    session = models.ForeignKey(
        ResponseSession, on_delete=models.CASCADE, related_name="answers"
    )
    value = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Answer #{self.pk}"
