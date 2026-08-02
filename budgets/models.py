from django.conf import settings
from django.db import models


class Budget(models.Model):
    """Ngân sách theo danh mục, theo tháng/năm."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets")
    category = models.ForeignKey("core.Category", on_delete=models.CASCADE, related_name="budgets")
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    limit_amount = models.DecimalField(max_digits=14, decimal_places=2)

    notified_80 = models.BooleanField(default=False)
    notified_100 = models.BooleanField(default=False)
    notified_over = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "category", "month", "year"], name="uq_budget_period")
        ]
        indexes = [models.Index(fields=["user", "year", "month"])]

    def __str__(self):
        return f"{self.category} - {self.month}/{self.year}: {self.limit_amount}"
