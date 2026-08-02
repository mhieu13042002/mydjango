from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.utils import timezone

from core.models import Category, Expense
from core.forms import models_q
from .models import Budget


@login_required
def budget_view(request):
    today = timezone.localdate()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    categories = Category.objects.filter(models_q(request.user), type="expense").order_by("name")

    if request.method == "POST":
        for cat in categories:
            field = f"limit_{cat.id}"
            val = request.POST.get(field, "").strip()
            existing = Budget.objects.filter(user=request.user, category=cat, month=month, year=year).first()
            if val:
                amount = float(val)
                if existing:
                    if float(existing.limit_amount) != amount:
                        existing.limit_amount = amount
                        existing.notified_80 = existing.notified_100 = existing.notified_over = False
                        existing.save()
                else:
                    Budget.objects.create(user=request.user, category=cat, month=month, year=year, limit_amount=amount)
            elif existing:
                existing.delete()
        messages.success(request, "Đã lưu ngân sách tháng này.")
        return redirect(f"/ngan-sach/?year={year}&month={month}")

    budgets = {b.category_id: b for b in Budget.objects.filter(user=request.user, month=month, year=year)}

    spent_qs = (Expense.objects.filter(user=request.user, type="expense", date__year=year, date__month=month)
                .values("category_id").annotate(total=Sum("amount")))
    spent_by_cat = {row["category_id"]: float(row["total"]) for row in spent_qs}

    rows = []
    for cat in categories:
        budget = budgets.get(cat.id)
        spent = spent_by_cat.get(cat.id, 0)
        limit = float(budget.limit_amount) if budget else 0
        ratio = round(spent / limit * 100, 0) if limit > 0 else 0
        rows.append({
            "category": cat, "limit": limit if limit else "", "spent": spent,
            "ratio": min(ratio, 100), "has_limit": limit > 0,
        })

    return render(request, "budgets/budget.html", {
        "rows": rows, "year": year, "month": month, "current_year": today.year,
        "month_range": range(1, 13), "year_range": range(today.year - 2, today.year + 1),
    })
