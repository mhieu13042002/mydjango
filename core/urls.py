from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),

    path("chi-tieu/", views.expense_list_view, name="expense_list"),
    path("chi-tieu/them/", views.expense_add_view, name="expense_add"),
    path("chi-tieu/them-anh/", views.expense_add_photo_view, name="expense_add_photo"),
    path("chi-tieu/<int:pk>/", views.expense_detail_view, name="expense_detail"),
    path("chi-tieu/<int:pk>/sua/", views.expense_edit_view, name="expense_edit"),
    path("chi-tieu/<int:pk>/xoa/", views.expense_delete_view, name="expense_delete"),
    path("chi-tieu/<int:pk>/doi-danh-muc/", views.api_update_expense_category, name="api_update_category"),

    path("api/phan-tich-anh/", views.api_analyze_image, name="api_analyze_image"),
    path("api/luu-chi-tieu-anh/", views.api_save_photo_expense, name="api_save_photo_expense"),
    path("api/goi-y-danh-muc/", views.api_suggest_category, name="api_suggest_category"),
    path("api/bieu-do/danh-muc/", views.api_chart_category, name="api_chart_category"),
    path("api/bieu-do/theo-thang/", views.api_chart_monthly, name="api_chart_monthly"),
    path("api/bieu-do/theo-ngay/", views.api_chart_daily, name="api_chart_daily"),
    path("api/goi-y-toi-uu/", views.api_optimization_tips, name="api_optimization_tips"),
]
