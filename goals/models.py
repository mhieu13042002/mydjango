from django.conf import settings
from django.db import models
from django.utils import timezone


class SavingGoal(models.Model):
    """Mục tiêu tiết kiệm: tên, số tiền mục tiêu, deadline, số đã tiết kiệm."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saving_goals")
    name = models.CharField(max_length=150)
    target_amount = models.DecimalField(max_digits=14, decimal_places=2)
    current_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    deadline = models.DateField()
    icon = models.CharField(max_length=10, default="🎯")
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["deadline"]

    def __str__(self):
        return self.name

    @property
    def progress_pct(self):
        if self.target_amount <= 0:
            return 0
        return min(100, round(float(self.current_amount) / float(self.target_amount) * 100, 1))

    @property
    def remaining_amount(self):
        return max(self.target_amount - self.current_amount, 0)

    @property
    def days_left(self):
        return max((self.deadline - timezone.localdate()).days, 0)

    @property
    def months_left(self):
        return max(self.days_left / 30.0, 1 / 30.0)

    @property
    def monthly_required(self):
        return round(float(self.remaining_amount) / self.months_left, 0)

    @property
    def daily_required(self):
        return round(float(self.remaining_amount) / max(self.days_left, 1), 0)


class GoalContribution(models.Model):
    """Lịch sử nạp tiền vào mục tiêu tiết kiệm."""
    goal = models.ForeignKey(SavingGoal, on_delete=models.CASCADE, related_name="contributions")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateField(default=timezone.localdate)
    note = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
