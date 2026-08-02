# -*- coding: utf-8 -*-
"""Các hàm phân tích tài chính: phát hiện bất thường, dự báo cuối tháng,
insight tổng quan, và gợi ý tối ưu chi tiêu. Thuần thống kê (numpy), chạy
nhanh, không phụ thuộc dịch vụ ngoài."""
from collections import defaultdict
from datetime import date
import calendar
import numpy as np


def _month_key(d):
    return (d.year, d.month)


def detect_anomaly_for_new_expense(user, expense, lookback_days=90):
    """Kiểm tra 1 khoản chi vừa nhập có bất thường so với lịch sử cùng danh
    mục hay không. Dùng cho luồng 'AI phát hiện chi tiêu bất thường' theo
    thời gian thực khi người dùng vừa lưu khoản chi."""
    from core.models import Expense

    history = Expense.objects.filter(
        user=user, type="expense", category=expense.category, is_special=False
    ).exclude(pk=expense.pk).order_by("-date")[:60]

    amounts = [float(e.amount) for e in history]
    if len(amounts) < 4:
        return None

    mean = float(np.mean(amounts))
    std = float(np.std(amounts))
    if mean <= 0:
        return None

    current = float(expense.amount)
    pct_over = (current - mean) / mean * 100

    if std > 0:
        z = (current - mean) / std
    else:
        z = 0

    if pct_over >= 80 or z >= 2.2:
        return {
            "average": round(mean, 0),
            "current": current,
            "pct_over": round(pct_over, 0),
            "z_score": round(z, 2),
        }
    return None


def detect_anomalies(expenses, z_threshold=2.0):
    """Quét toàn bộ danh sách giao dịch để tìm các khoản bất thường theo
    từng danh mục (dùng cho dashboard tổng quan)."""
    by_cat = defaultdict(list)
    for e in expenses:
        if e.type == "expense" and not e.is_special:
            by_cat[e.category_id].append(e)

    anomalies = []
    for cat_id, items in by_cat.items():
        if len(items) < 4:
            continue
        amounts = np.array([float(e.amount) for e in items])
        mean, std = amounts.mean(), amounts.std()
        if std == 0:
            continue
        for e in items:
            z = (float(e.amount) - mean) / std
            if z >= z_threshold:
                anomalies.append({
                    "id": e.id,
                    "title": e.title,
                    "date": e.date.isoformat(),
                    "category": e.category.name,
                    "icon": e.category.icon,
                    "amount": float(e.amount),
                    "z_score": round(float(z), 2),
                    "avg_amount": round(float(mean), 0),
                    "pct_over": round((float(e.amount) - mean) / mean * 100, 0) if mean else 0,
                })
    anomalies.sort(key=lambda a: -a["z_score"])
    return anomalies[:10]


def forecast_month_end(expenses, year, month):
    """Dự báo tổng chi tiêu CUỐI THÁNG hiện tại, dựa trên tốc độ chi tiêu từ
    đầu tháng đến hôm nay (nếu là tháng hiện tại) hoặc xu hướng các tháng
    gần nhất (nếu xem tháng khác)."""
    today = date.today()
    days_in_month = calendar.monthrange(year, month)[1]

    month_expenses = [e for e in expenses if e.type == "expense" and _month_key(e.date) == (year, month)]
    spent_so_far = sum(float(e.amount) for e in month_expenses)

    if (year, month) == (today.year, today.month) and today.day > 0:
        daily_rate = spent_so_far / today.day
        predicted = daily_rate * days_in_month
        trend_basis = "daily_rate"
    else:
        predicted = spent_so_far
        trend_basis = "actual"

    # Xu hướng dựa trên các tháng trước để đối chiếu
    monthly_totals = defaultdict(float)
    for e in expenses:
        if e.type == "expense":
            monthly_totals[_month_key(e.date)] += float(e.amount)
    past_months = sorted(k for k in monthly_totals if k < (year, month))[-3:]
    avg_past = np.mean([monthly_totals[k] for k in past_months]) if past_months else None

    trend = "stable"
    if avg_past:
        if predicted > avg_past * 1.1:
            trend = "up"
        elif predicted < avg_past * 0.9:
            trend = "down"

    return {
        "predicted": round(max(predicted, 0), 0),
        "spent_so_far": round(spent_so_far, 0),
        "days_in_month": days_in_month,
        "trend": trend,
        "avg_past_months": round(avg_past, 0) if avg_past else None,
        "basis": trend_basis,
    }


def generate_insights(expenses, budgets=None, income_total=0):
    """Sinh nhận xét tổng quan ngắn gọn cho Dashboard, kiểu:
    'Bạn đang chi nhiều cho Ăn uống hơn tháng trước 18%.'"""
    insights = []
    if not expenses:
        return [{"level": "info", "icon": "👋", "text": "Chưa có dữ liệu chi tiêu. Hãy thêm khoản chi đầu tiên!"}]

    today = date.today()
    cur_key = (today.year, today.month)
    prev_month = today.month - 1 or 12
    prev_year = today.year if today.month > 1 else today.year - 1
    prev_key = (prev_year, prev_month)

    cur_by_cat = defaultdict(float)
    prev_by_cat = defaultdict(float)
    cur_expense_total = 0.0

    for e in expenses:
        if e.type != "expense":
            continue
        key = _month_key(e.date)
        if key == cur_key:
            cur_by_cat[e.category.name] += float(e.amount)
            cur_expense_total += float(e.amount)
        elif key == prev_key:
            prev_by_cat[e.category.name] += float(e.amount)

    # So sánh từng danh mục tháng này với tháng trước -> câu insight mẫu trong đặc tả
    comparisons = []
    for cat_name, cur_amt in cur_by_cat.items():
        prev_amt = prev_by_cat.get(cat_name, 0)
        if prev_amt > 0:
            change = (cur_amt - prev_amt) / prev_amt * 100
            comparisons.append((cat_name, change, cur_amt))
    comparisons.sort(key=lambda c: -abs(c[1]))

    for cat_name, change, _ in comparisons[:2]:
        if change >= 15:
            insights.append({"level": "warning", "icon": "📈",
                              "text": f"Bạn đang chi nhiều cho {cat_name} hơn tháng trước {change:.0f}%."})
        elif change <= -15:
            insights.append({"level": "success", "icon": "📉",
                              "text": f"Bạn đã chi ít hơn cho {cat_name} so với tháng trước {abs(change):.0f}%."})

    # Tỉ lệ tiết kiệm
    if income_total > 0:
        savings_rate = (income_total - cur_expense_total) / income_total * 100
        if savings_rate < 0:
            insights.append({"level": "danger", "icon": "🚨",
                              "text": f"Chi tiêu tháng này đã vượt thu nhập {abs(savings_rate):.0f}%."})
        elif savings_rate < 10:
            insights.append({"level": "warning", "icon": "💡",
                              "text": f"Tỉ lệ tiết kiệm tháng này chỉ {savings_rate:.0f}%, nên cân đối lại chi tiêu."})
        else:
            insights.append({"level": "success", "icon": "🎯",
                              "text": f"Tỉ lệ tiết kiệm tháng này đạt {savings_rate:.0f}% — rất tốt!"})

    # Danh mục chi nhiều nhất
    if cur_by_cat:
        top_cat = max(cur_by_cat, key=cur_by_cat.get)
        top_pct = cur_by_cat[top_cat] / cur_expense_total * 100 if cur_expense_total else 0
        insights.append({"level": "info", "icon": "🏆",
                          "text": f"\"{top_cat}\" đang là danh mục chi nhiều nhất, chiếm {top_pct:.0f}% tổng chi tiêu tháng này."})

    if budgets:
        for b in budgets:
            spent = cur_by_cat.get(b.category.name, 0)
            if b.limit_amount > 0:
                ratio = spent / float(b.limit_amount) * 100
                if ratio >= 100:
                    insights.append({"level": "danger", "icon": "🚨",
                                      "text": f"Ngân sách \"{b.category.name}\" đã vượt {ratio-100:.0f}%."})
                elif ratio >= 80:
                    insights.append({"level": "warning", "icon": "⏰",
                                      "text": f"Ngân sách \"{b.category.name}\" đã dùng {ratio:.0f}%, sắp chạm giới hạn."})

    return insights[:6]


def generate_optimization_tips(expenses, min_tips=5):
    """Đưa ra tối thiểu N gợi ý tối ưu chi tiêu, theo mẫu trong đặc tả:
    'Nếu giảm 20% số chuyến Grab bạn sẽ tiết kiệm khoảng 320.000 mỗi tháng.'"""
    today = date.today()
    cur_key = (today.year, today.month)

    # Nhóm theo (title chuẩn hoá, category) để phát hiện các khoản lặp lại
    groups = defaultdict(list)
    for e in expenses:
        if e.type == "expense" and _month_key(e.date) == cur_key:
            key = (e.title.strip().lower(), e.category.name)
            groups[key].append(float(e.amount))

    tips = []
    # Ưu tiên các khoản lặp lại nhiều lần trong tháng (thói quen chi tiêu)
    candidates = [(k, v) for k, v in groups.items() if len(v) >= 3]
    candidates.sort(key=lambda kv: -sum(kv[1]))

    for (title, cat_name), amounts in candidates:
        count = len(amounts)
        total = sum(amounts)
        reduce_ratio = 0.2 if count >= 8 else 0.3
        save_amount = total * reduce_ratio
        new_count = max(round(count * (1 - reduce_ratio)), 1)
        tips.append({
            "icon": "💡",
            "text": (f"\"{title.capitalize()}\" ({cat_name}) bạn chi {count} lần trong tháng, "
                     f"tổng {total:,.0f}đ. Nếu giảm xuống còn {new_count} lần, "
                     f"bạn sẽ tiết kiệm khoảng {save_amount:,.0f}đ mỗi tháng."),
        })
        if len(tips) >= min_tips:
            break

    # Nếu chưa đủ số gợi ý, bổ sung theo danh mục có tổng chi lớn
    if len(tips) < min_tips:
        cat_totals = defaultdict(float)
        cat_counts = defaultdict(int)
        for e in expenses:
            if e.type == "expense" and _month_key(e.date) == cur_key:
                cat_totals[e.category.name] += float(e.amount)
                cat_counts[e.category.name] += 1
        sorted_cats = sorted(cat_totals.items(), key=lambda kv: -kv[1])
        for cat_name, total in sorted_cats:
            if len(tips) >= min_tips:
                break
            if any(cat_name in t["text"] for t in tips):
                continue
            save_amount = total * 0.15
            tips.append({
                "icon": "💡",
                "text": (f"Danh mục \"{cat_name}\" đang chiếm {total:,.0f}đ tháng này. "
                         f"Giảm chi tiêu 15% ở danh mục này giúp bạn tiết kiệm khoảng {save_amount:,.0f}đ."),
            })

    # Gợi ý chung nếu vẫn chưa đủ (đảm bảo tối thiểu min_tips)
    generic_tips = [
        "Thử áp dụng quy tắc 50/30/20: 50% nhu cầu thiết yếu, 30% mong muốn, 20% tiết kiệm.",
        "Đặt ngân sách cho từng danh mục sẽ giúp bạn kiểm soát chi tiêu chủ động hơn.",
        "Ghi chép chi tiêu hằng ngày giúp AI phân tích chính xác hơn theo thời gian.",
        "Xem lại các khoản đăng ký định kỳ (subscription) mà bạn ít dùng để cắt giảm.",
        "So sánh giá trước khi mua sắm các khoản lớn để tối ưu ngân sách.",
    ]
    i = 0
    while len(tips) < min_tips and i < len(generic_tips):
        tips.append({"icon": "✨", "text": generic_tips[i]})
        i += 1

    return tips[:max(min_tips, len(tips))]
