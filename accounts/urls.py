from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from . import views

app_name = "accounts"

urlpatterns = [
    path("dang-ky/", views.register_view, name="register"),
    path("dang-nhap/", auth_views.LoginView.as_view(
        template_name="accounts/login.html", redirect_authenticated_user=True), name="login"),
    path("dang-xuat/", auth_views.LogoutView.as_view(), name="logout"),
    path("ho-so/", views.profile_view, name="profile"),
    path("doi-mat-khau/", views.SmartPasswordChangeView.as_view(), name="change_password"),

    # Quên mật khẩu - flow chuẩn Django, gửi email theo EMAIL_BACKEND đã cấu hình trong .env
    path("quen-mat-khau/", auth_views.PasswordResetView.as_view(
        template_name="accounts/password_reset.html",
        email_template_name="accounts/password_reset_email.html",
        subject_template_name="accounts/password_reset_subject.txt",
        success_url=reverse_lazy("accounts:password_reset_done"),
    ), name="password_reset"),
    path("quen-mat-khau/da-gui/", auth_views.PasswordResetDoneView.as_view(
        template_name="accounts/password_reset_done.html"), name="password_reset_done"),
    path("dat-lai-mat-khau/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/password_reset_confirm.html",
        success_url=reverse_lazy("accounts:password_reset_complete"),
    ), name="password_reset_confirm"),
    path("dat-lai-mat-khau/hoan-tat/", auth_views.PasswordResetCompleteView.as_view(
        template_name="accounts/password_reset_complete.html"), name="password_reset_complete"),
]
