from django.contrib import admin
from .models import Budget


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "month", "year", "limit_amount")
    list_filter = ("year", "month")
    list_select_related = ("user", "category")
