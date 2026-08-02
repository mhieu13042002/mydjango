"""Service layer — tách logic nghiệp vụ khỏi view, tuân thủ Clean Architecture/SRP.
Các hàm ở đây được gọi từ view của nhiều app khác nhau (core, budgets, goals)."""
from datetime import date


def notify(user, type_, title, message, level="info", icon="🔔", link=""):
    """Tạo 1 thông báo cho người dùng. Import trễ (lazy import) để tránh
    vòng lặp phụ thuộc giữa app notifications và core/budgets/goals."""
    from notifications.models import Notification
    return Notification.objects.create(
        user=user, type=type_, title=title, message=message,
        level=level, icon=icon, link=link,
    )


def check_budget_after_expense(expense):
    """Sau khi lưu 1 khoản chi, kiểm tra ngân sách danh mục tương ứng của
    tháng hiện tại của khoản chi và tạo thông báo nếu đạt 80% / 100% / vượt."""
    from budgets.models import Budget
    from core.models import Expense

    if expense.type != "expense":
        return

    budget = Budget.objects.filter(
        user=expense.user, category=expense.category,
        month=expense.date.month, year=expense.date.year,
    ).first()
    if not budget or budget.limit_amount <= 0:
        return

    spent = Expense.objects.filter(
        user=expense.user, category=expense.category, type="expense",
        date__year=expense.date.year, date__month=expense.date.month,
    ).values_list("amount", flat=True)
    total_spent = sum(float(a) for a in spent)
    ratio = total_spent / float(budget.limit_amount)

    if ratio >= 1.0 and not budget.notified_over:
        notify(expense.user, "budget_over",
               "Đã vượt ngân sách!",
               f"Danh mục \"{expense.category.name}\" đã vượt ngân sách tháng {expense.date.month} "
               f"({total_spent:,.0f}đ / {float(budget.limit_amount):,.0f}đ).",
               level="danger", icon="🚨")
        budget.notified_over = True
        budget.notified_100 = True
        budget.notified_80 = True
        budget.save(update_fields=["notified_over", "notified_100", "notified_80"])
    elif ratio >= 1.0 and not budget.notified_100:
        notify(expense.user, "budget_100", "Đạt 100% ngân sách",
               f"Danh mục \"{expense.category.name}\" đã đạt giới hạn ngân sách tháng này.",
               level="danger", icon="⛔")
        budget.notified_100 = True
        budget.save(update_fields=["notified_100"])
    elif ratio >= 0.8 and not budget.notified_80:
        notify(expense.user, "budget_80", "Sắp đạt giới hạn ngân sách",
               f"Danh mục \"{expense.category.name}\" đã dùng {ratio*100:.0f}% ngân sách tháng này.",
               level="warning", icon="⏰")
        budget.notified_80 = True
        budget.save(update_fields=["notified_80"])


def check_anomaly_after_expense(expense):
    """Kiểm tra khoản chi vừa lưu có bất thường không, nếu có thì tạo thông báo."""
    from ai_engine.analytics import detect_anomaly_for_new_expense

    if expense.type != "expense" or expense.is_special:
        return None

    result = detect_anomaly_for_new_expense(expense.user, expense)
    if result:
        notify(
            expense.user, "anomaly", "Phát hiện chi tiêu bất thường",
            f"Hôm nay bạn chi cho \"{expense.category.name}\" cao hơn trung bình "
            f"{result['pct_over']:.0f}% (bình thường ~{result['average']:,.0f}đ).",
            level="warning", icon="🔍",
        )
    return result
