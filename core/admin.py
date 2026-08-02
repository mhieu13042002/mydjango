from django.contrib import admin
from .models import Category, Expense, ExpenseImage, AIAnalysis, AuditLog


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "icon", "user", "is_system")
    list_filter = ("type", "is_system")
    search_fields = ("name",)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "category", "type", "amount", "date", "is_special")
    list_filter = ("type", "is_special", "category")
    search_fields = ("title", "note")
    date_hierarchy = "date"
    list_select_related = ("user", "category")


@admin.register(ExpenseImage)
class ExpenseImageAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "expense", "created_at")


@admin.register(AIAnalysis)
class AIAnalysisAdmin(admin.ModelAdmin):
    list_display = ("id", "detected_label", "suggested_category", "confidence")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "action", "method", "ip_address")
    list_filter = ("method",)
    date_hierarchy = "created_at"
