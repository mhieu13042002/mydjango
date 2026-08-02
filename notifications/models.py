from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPE_CHOICES = (
        ("budget_80", "Ngân sách đạt 80%"),
        ("budget_100", "Ngân sách đạt 100%"),
        ("budget_over", "Vượt ngân sách"),
        ("goal_reached", "Đạt mục tiêu tiết kiệm"),
        ("anomaly", "Chi tiêu bất thường"),
        ("ai_tip", "Gợi ý AI"),
        ("system", "Hệ thống"),
    )
    LEVEL_CHOICES = (("info", "Thông tin"), ("warning", "Cảnh báo"), ("danger", "Nguy hiểm"), ("success", "Thành công"))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="system")
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default="info")
    icon = models.CharField(max_length=10, default="🔔")
    title = models.CharField(max_length=150)
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return self.title
