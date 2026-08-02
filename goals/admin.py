from django.contrib import admin
from .models import SavingGoal, GoalContribution


class ContributionInline(admin.TabularInline):
    model = GoalContribution
    extra = 0


@admin.register(SavingGoal)
class SavingGoalAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "target_amount", "current_amount", "deadline", "is_completed")
    list_filter = ("is_completed",)
    inlines = [ContributionInline]
