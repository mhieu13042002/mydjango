from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from core.services import notify
from .models import SavingGoal, GoalContribution
from .forms import SavingGoalForm, GoalContributionForm


@login_required
def goal_list_view(request):
    goals = SavingGoal.objects.filter(user=request.user)
    return render(request, "goals/goal_list.html", {"goals": goals})


@login_required
def goal_add_view(request):
    if request.method == "POST":
        form = SavingGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, "Đã tạo mục tiêu tiết kiệm mới!")
            return redirect("goals:goal_list")
    else:
        form = SavingGoalForm(initial={"deadline": timezone.localdate()})
    return render(request, "goals/goal_form.html", {"form": form})


@login_required
def goal_detail_view(request, pk):
    goal = get_object_or_404(SavingGoal, pk=pk, user=request.user)
    if request.method == "POST":
        form = GoalContributionForm(request.POST)
        if form.is_valid():
            contribution = form.save(commit=False)
            contribution.goal = goal
            contribution.save()
            goal.current_amount = float(goal.current_amount) + float(contribution.amount)
            if goal.current_amount >= goal.target_amount and not goal.is_completed:
                goal.is_completed = True
                notify(request.user, "goal_reached", "🎉 Đạt mục tiêu tiết kiệm!",
                       f"Chúc mừng! Bạn đã hoàn thành mục tiêu \"{goal.name}\".",
                       level="success", icon="🎉")
            goal.save()
            messages.success(request, "Đã cập nhật số tiền tiết kiệm.")
            return redirect("goals:goal_detail", pk=goal.pk)
    else:
        form = GoalContributionForm(initial={"date": timezone.localdate()})

    contributions = goal.contributions.all()[:20]
    return render(request, "goals/goal_detail.html", {"goal": goal, "form": form, "contributions": contributions})


@login_required
def goal_delete_view(request, pk):
    goal = get_object_or_404(SavingGoal, pk=pk, user=request.user)
    if request.method == "POST":
        goal.delete()
        messages.success(request, "Đã xoá mục tiêu.")
    return redirect("goals:goal_list")
