from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter(name="vnd")
def vnd(value):
    """
    Hiển thị số tiền kiểu Việt Nam với dấu chấm ngăn cách hàng nghìn.
    Ví dụ: 100000 -> "100.000", 1500000 -> "1.500.000"
    Dùng trong template: {{ expense.amount|vnd }}đ
    """
    if value in (None, ""):
        return "0"
    try:
        num = int(Decimal(str(value)).quantize(Decimal("1")))
    except (InvalidOperation, ValueError, TypeError):
        return value
    sign = "-" if num < 0 else ""
    digits = str(abs(num))
    groups = []
    while digits:
        groups.insert(0, digits[-3:])
        digits = digits[:-3]
    return f"{sign}{'.'.join(groups)}"
