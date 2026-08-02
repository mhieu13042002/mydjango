from django.core.management.base import BaseCommand
from core.models import Category

DEFAULT_CATEGORIES = [
    ("Ăn uống", "expense", "🍜", "#f97316"),
    ("Di chuyển", "expense", "🚗", "#3b82f6"),
    ("Nhà ở", "expense", "🏠", "#8b5cf6"),
    ("Hóa đơn & Tiện ích", "expense", "🧾", "#ef4444"),
    ("Mua sắm", "expense", "🛍️", "#ec4899"),
    ("Giải trí", "expense", "🎬", "#06b6d4"),
    ("Y tế", "expense", "💊", "#10b981"),
    ("Giáo dục", "expense", "📚", "#eab308"),
    ("Khác", "expense", "📦", "#6b7280"),
    ("Lương", "income", "💼", "#22c55e"),
    ("Thưởng", "income", "🎁", "#14b8a6"),
    ("Thu nhập khác", "income", "💵", "#84cc16"),
]


class Command(BaseCommand):
    help = "Tạo danh mục thu/chi mặc định (dùng chung cho mọi người dùng, user=None)"

    def handle(self, *args, **options):
        created = 0
        for name, ctype, icon, color in DEFAULT_CATEGORIES:
            _, was_created = Category.objects.get_or_create(
                user=None, name=name, type=ctype,
                defaults={"icon": icon, "color": color, "is_system": True},
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Đã tạo {created} danh mục mặc định (tổng {len(DEFAULT_CATEGORIES)})."))
