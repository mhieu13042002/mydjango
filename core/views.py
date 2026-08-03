import os
import json
import calendar
from datetime import datetime, date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET

from .models import Category, Expense, ExpenseImage, AIAnalysis
from .forms import ExpenseForm, ExpenseImageUploadForm, models_q
from .services import check_budget_after_expense, check_anomaly_after_expense
from ai_engine import analytics, categorizer, image_recognition, image_annotate, gemini_vision


# --------------------------------------------------------------- helpers ---
def _user_categories(user, type_=None):
    qs = Category.objects.filter(models_q(user))
    if type_:
        qs = qs.filter(type=type_)
    return qs.order_by("name")


def _month_expenses_qs(user, year, month):
    return Expense.objects.filter(user=user, date__year=year, date__month=month).select_related("category")


# -------------------------------------------------------------- dashboard --
@login_required
def dashboard_view(request):
    today = timezone.localdate()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    month_qs = _month_expenses_qs(request.user, year, month)
    income_total = month_qs.filter(type="income").aggregate(s=Sum("amount"))["s"] or 0
    expense_total = month_qs.filter(type="expense").aggregate(s=Sum("amount"))["s"] or 0
    balance = float(income_total) - float(expense_total)
    savings_rate = (balance / float(income_total) * 100) if income_total else 0

    all_expenses = list(Expense.objects.filter(user=request.user).select_related("category").order_by("-date")[:400])

    from budgets.models import Budget
    budgets = list(Budget.objects.filter(user=request.user, year=year, month=month).select_related("category"))

    insights = analytics.generate_insights(all_expenses, budgets=budgets, income_total=float(income_total))
    anomalies = analytics.detect_anomalies([e for e in all_expenses if (e.date.year, e.date.month) == (year, month)])
    forecast = analytics.forecast_month_end(all_expenses, year, month)

    from goals.models import SavingGoal
    active_goal = SavingGoal.objects.filter(user=request.user, is_completed=False).order_by("deadline").first()

    recent = Expense.objects.filter(user=request.user).select_related("category").order_by("-date", "-created_at")[:5]

    context = {
        "year": year, "month": month, "today": today,
        "income_total": income_total, "expense_total": expense_total,
        "balance": balance, "savings_rate": savings_rate,
        "insights": insights, "anomalies": anomalies, "forecast": forecast,
        "recent": recent, "active_goal": active_goal,
        "years_range": range(today.year - 3, today.year + 1),
    }
    return render(request, "core/dashboard.html", context)


# --------------------------------------------------------------- expenses --
@login_required
def expense_list_view(request):
    qs = Expense.objects.filter(user=request.user).select_related("category")

    search = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")
    type_filter = request.GET.get("type", "")
    date_filter_type = request.GET.get("date_type", "")
    year = request.GET.get("year", "")
    month = request.GET.get("month", "")
    min_amount = request.GET.get("min_amount", "")
    max_amount = request.GET.get("max_amount", "")

    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(note__icontains=search))
    if category_id:
        qs = qs.filter(category_id=category_id)
    if type_filter in ("income", "expense"):
        qs = qs.filter(type=type_filter)
    if date_filter_type == "year" and year:
        qs = qs.filter(date__year=year)
    elif date_filter_type == "month" and year and month:
        qs = qs.filter(date__year=year, date__month=month)
    if min_amount:
        qs = qs.filter(amount__gte=min_amount)
    if max_amount:
        qs = qs.filter(amount__lte=max_amount)

    paginator = Paginator(qs, 9)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    context = {
        "page_obj": page_obj,
        "categories": _user_categories(request.user),
        "search": search, "category_id": category_id, "type_filter": type_filter,
        "date_filter_type": date_filter_type, "year": year, "month": month,
        "min_amount": min_amount, "max_amount": max_amount,
        "current_year": timezone.localdate().year,
    }
    return render(request, "core/expense_list.html", context)


@login_required
def expense_add_view(request):
    """Thêm chi tiêu thủ công."""
    if request.method == "POST":
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            check_budget_after_expense(expense)
            anomaly = check_anomaly_after_expense(expense)
            messages.success(request, "Đã thêm khoản chi tiêu thành công!")
            if anomaly:
                messages.warning(
                    request,
                    f"⚠️ Khoản chi này cao hơn trung bình {anomaly['pct_over']:.0f}% so với thường lệ.",
                )
            return redirect("core:expense_list")
    else:
        form = ExpenseForm(user=request.user, initial={"date": timezone.localdate()})
    return render(request, "core/expense_form.html", {"form": form, "mode": "manual"})


@login_required
def expense_edit_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật khoản chi tiêu.")
            return redirect("core:expense_list")
    else:
        form = ExpenseForm(instance=expense, user=request.user)
    return render(request, "core/expense_form.html", {"form": form, "mode": "edit", "expense": expense})


@login_required
@require_POST
def expense_delete_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    expense.delete()
    messages.success(request, "Đã xoá khoản chi tiêu.")
    return redirect("core:expense_list")


@login_required
def expense_detail_view(request, pk):
    expense = get_object_or_404(Expense.objects.select_related("category"), pk=pk, user=request.user)
    image = getattr(expense, "image", None)
    return render(request, "core/expense_detail.html", {"expense": expense, "image": image})


# ---------------------------------------------------------- photo upload ---
@login_required
def expense_add_photo_view(request):
    """Trang thêm chi tiêu bằng ảnh: upload -> AI phân tích (AJAX) -> preview
    -> người dùng nhập số tiền -> lưu (AJAX, không reload)."""
    return render(request, "core/expense_form_photo.html", {
        "categories": _user_categories(request.user, "expense"),
    })


@login_required
@require_POST
def api_analyze_image(request):
    """Nhận ảnh, chạy AI nhận diện, trả về preview + gợi ý danh mục.
    Ảnh gốc được lưu tạm ngay (ExpenseImage chưa gắn Expense) để bước sau
    dùng lại mà không phải upload lại.

    Ưu tiên gọi Gemini Vision (chính xác hơn, đọc được chữ trên hoá đơn) nếu
    đã cấu hình GEMINI_API_KEY; nếu chưa cấu hình hoặc Gemini gọi lỗi (mất
    mạng, hết quota...), tự động dùng lại model offline cũ để app không bao
    giờ bị đứng vì lý do bên thứ ba."""
    form = ExpenseImageUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    image_obj = ExpenseImage.objects.create(user=request.user, original_image=form.cleaned_data["image"])
    image_path = image_obj.original_image.path

    expense_categories = list(_user_categories(request.user, "expense"))
    category_names = [c.name for c in expense_categories]

    gemini_result = gemini_vision.analyze_expense_image(image_path, category_names)

    suggested_title = ""
    suggested_amount = None

    if gemini_result is not None:
        result = gemini_result
        label_vi = result["label"] or "Không xác định rõ"
        suggested_title = result.get("suggested_title") or ""
        suggested_amount = result.get("suggested_amount")
    else:
        result = image_recognition.recognize_image(image_path)
        label_vi = image_recognition.label_to_vietnamese(result["label"])

    suggested_category = None
    if result["category"]:
        suggested_category = Category.objects.filter(
            models_q(request.user), name=result["category"], type="expense"
        ).first()

    AIAnalysis.objects.create(
        image=image_obj,
        detected_label=result["label"] or "",
        suggested_category=suggested_category,
        confidence=result["confidence"],
        raw_result=result,
    )

    categories = [{"id": c.id, "name": c.name, "icon": c.icon} for c in expense_categories]

    return JsonResponse({
        "ok": True,
        "image_id": image_obj.id,
        "image_url": image_obj.original_image.url,
        "detected_label": label_vi,
        "raw_label": result["label"],
        "confidence": round(result["confidence"], 2),
        "suggested_category_id": suggested_category.id if suggested_category else None,
        "suggested_category_name": suggested_category.name if suggested_category else None,
        "suggested_title": suggested_title,
        "suggested_amount": suggested_amount,
        "categories": categories,
        "has_detection": bool(result["label"]),
        "auto_suggest": bool(result.get("auto_suggest")),
        "ai_source": result.get("source", "offline"),
    })


@login_required
@require_POST
def api_save_photo_expense(request):
    """Hoàn tất lưu khoản chi từ ảnh: nhận amount + category + ngày + ghi chú,
    dùng Pillow ghi số tiền/ngày lên ảnh, tạo Expense + gắn ảnh đã chú thích."""
    try:
        image_id = int(request.POST.get("image_id"))
        amount = float(request.POST.get("amount"))
        category_id = int(request.POST.get("category_id"))
        title = request.POST.get("title", "").strip() or "Chi tiêu từ ảnh"
        expense_date_str = request.POST.get("date", "")
        note = request.POST.get("note", "").strip()
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "Dữ liệu không hợp lệ."}, status=400)

    if amount <= 0:
        return JsonResponse({"ok": False, "error": "Số tiền phải lớn hơn 0."}, status=400)

    image_obj = get_object_or_404(ExpenseImage, pk=image_id, user=request.user)
    category = get_object_or_404(Category, pk=category_id)

    try:
        expense_date = datetime.strptime(expense_date_str, "%Y-%m-%d").date()
    except ValueError:
        expense_date = timezone.localdate()

    expense = Expense.objects.create(
        user=request.user, title=title, category=category, type="expense",
        amount=amount, date=expense_date, note=note,
    )

    # Ghi số tiền + ngày lên ảnh bằng Pillow, lưu thành ảnh mới
    output_dir = os.path.join(settings.MEDIA_ROOT, "expenses", str(request.user.id))
    output_filename = f"annotated_{expense.id}_{os.path.basename(image_obj.original_image.name)}"
    output_path = os.path.join(output_dir, output_filename)
    amount_text = f"{amount:,.0f} VNĐ"
    date_text = expense_date.strftime("%d/%m/%Y")
    image_annotate.annotate_expense_image(image_obj.original_image.path, output_path, amount_text, date_text)

    image_obj.expense = expense
    image_obj.annotated_image.name = os.path.relpath(output_path, settings.MEDIA_ROOT)
    image_obj.save(update_fields=["expense", "annotated_image"])

    check_budget_after_expense(expense)
    anomaly = check_anomaly_after_expense(expense)

    return JsonResponse({
        "ok": True,
        "expense_id": expense.id,
        "redirect_url": reverse("core:expense_list"),
        "anomaly": anomaly,
    })


@login_required
@require_POST
def api_update_expense_category(request, pk):
    """Cho phép người dùng đổi danh mục ngay nếu AI nhận diện sai (theo đặc tả)."""
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    category_id = request.POST.get("category_id")
    category = get_object_or_404(Category, pk=category_id)
    expense.category = category
    expense.save(update_fields=["category"])
    return JsonResponse({"ok": True, "category_name": category.name, "icon": category.icon})


# -------------------------------------------------------------------- API --
@login_required
@require_GET
def api_suggest_category(request):
    description = request.GET.get("description", "")
    type_ = request.GET.get("type", "expense")
    valid_names = set(_user_categories(request.user, type_).values_list("name", flat=True))
    name, confidence = categorizer.suggest_category_from_text(description, valid_names)
    cat = _user_categories(request.user, type_).filter(name=name).first() if name else None
    return JsonResponse({
        "category": name, "category_id": cat.id if cat else None,
        "icon": cat.icon if cat else None, "confidence": confidence,
    })


@login_required
@require_GET
def api_chart_category(request):
    today = timezone.localdate()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))
    qs = _month_expenses_qs(request.user, year, month).filter(type="expense")
    totals = {}
    colors = {}
    for e in qs:
        totals[e.category.name] = totals.get(e.category.name, 0) + float(e.amount)
        colors[e.category.name] = e.category.color
    labels = list(totals.keys())
    return JsonResponse({"labels": labels, "data": [totals[l] for l in labels], "colors": [colors[l] for l in labels]})


@login_required
@require_GET
def api_chart_monthly(request):
    today = timezone.localdate()
    year = int(request.GET.get("year", today.year))
    months, income_vals, expense_vals = [], [], []
    for m in range(1, 13):
        qs = _month_expenses_qs(request.user, year, m)
        income_vals.append(float(qs.filter(type="income").aggregate(s=Sum("amount"))["s"] or 0))
        expense_vals.append(float(qs.filter(type="expense").aggregate(s=Sum("amount"))["s"] or 0))
        months.append(f"T{m}")
    return JsonResponse({"labels": months, "income": income_vals, "expense": expense_vals})


@login_required
@require_GET
def api_chart_daily(request):
    today = timezone.localdate()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))
    days_in_month = calendar.monthrange(year, month)[1]
    qs = _month_expenses_qs(request.user, year, month).filter(type="expense")
    daily = {d: 0.0 for d in range(1, days_in_month + 1)}
    for e in qs:
        daily[e.date.day] = daily.get(e.date.day, 0) + float(e.amount)
    return JsonResponse({"labels": [str(d) for d in daily.keys()], "data": list(daily.values())})


@login_required
@require_GET
def api_optimization_tips(request):
    expenses = list(Expense.objects.filter(user=request.user).select_related("category"))
    tips = analytics.generate_optimization_tips(expenses)
    return JsonResponse({"tips": tips})
