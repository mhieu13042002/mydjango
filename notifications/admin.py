from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "type", "level", "is_read", "created_at")
    list_filter = ("type", "level", "is_read")
