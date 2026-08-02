import os
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


def expense_image_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"expenses/{instance.user_id}/{uuid.uuid4().hex}{ext}"


class Category(models.Model):
    """Danh mục thu/chi. Có sẵn danh mục hệ thống (user=None) và danh mục
    người dùng tự tạo."""
    TYPE_CHOICES = (("expense", "Chi tiêu"), ("income", "Thu nhập"))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=60)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, db_index=True)
    icon = models.CharField(max_length=10, default="💰")
    color = models.CharField(max_length=20, default="#6366f1")
    is_system = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["type", "user"])]
        constraints = [
            models.UniqueConstraint(fields=["user", "name", "type"], name="uq_category_per_user")
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name


class Expense(models.Model):
    """Khoản chi tiêu. type phân biệt Chi (expense) / Thu (income) để dùng
    chung 1 bảng giao dịch, đơn giản hoá truy vấn báo cáo tổng hợp."""
    TYPE_CHOICES = (("expense", "Chi tiêu"), ("income", "Thu nhập"))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="expenses")
    title = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="expenses")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="expense", db_index=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateField(default=timezone.now, db_index=True)
    note = models.TextField(blank=True, default="")

    is_special = models.BooleanField(default=False, help_text="Người dùng xác nhận đây là khoản chi đặc biệt (bỏ qua cảnh báo bất thường)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["user", "type", "date"]),
            models.Index(fields=["user", "category"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.amount}"


class ExpenseImage(models.Model):
    """Ảnh gốc + ảnh đã chú thích số tiền/ngày (do Pillow ghi đè) cho một khoản chi."""
    expense = models.OneToOneField(Expense, on_delete=models.CASCADE, related_name="image", null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="expense_images")

    original_image = models.ImageField(upload_to=expense_image_upload_path)
    annotated_image = models.ImageField(upload_to=expense_image_upload_path, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ảnh #{self.pk}"


class AIAnalysis(models.Model):
    """Kết quả AI phân tích 1 ảnh: nhãn nhận diện, danh mục gợi ý, độ tin cậy."""
    image = models.OneToOneField(ExpenseImage, on_delete=models.CASCADE, related_name="analysis")
    detected_label = models.CharField(max_length=100, blank=True, default="")
    suggested_category = models.ForeignKey(Category, null=True, blank=True,
                                            on_delete=models.SET_NULL, related_name="+")
    confidence = models.FloatField(default=0.0)
    raw_result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AI: {self.detected_label} ({self.confidence:.0%})"


class AuditLog(models.Model):
    """Nhật ký thao tác quan trọng của người dùng (thêm/sửa/xoá dữ liệu tài chính, đăng nhập...)."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="audit_logs")
    action = models.CharField(max_length=50, db_index=True)
    object_repr = models.CharField(max_length=255, blank=True, default="")
    path = models.CharField(max_length=255, blank=True, default="")
    method = models.CharField(max_length=10, blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.action}"
