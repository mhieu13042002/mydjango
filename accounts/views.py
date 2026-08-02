from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from .forms import RegisterForm, ProfileUpdateForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Chào mừng {user.first_name}! Tài khoản đã được tạo thành công.")
            return redirect("core:dashboard")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile_view(request):
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            request.user.first_name = form.cleaned_data["first_name"]
            request.user.email = form.cleaned_data["email"]
            request.user.save()
            form.save()
            messages.success(request, "Đã cập nhật hồ sơ thành công.")
            return redirect("accounts:profile")
    else:
        form = ProfileUpdateForm(instance=profile, initial={
            "first_name": request.user.first_name, "email": request.user.email,
        })
    return render(request, "accounts/profile.html", {"form": form, "profile": profile})


class SmartPasswordChangeView(PasswordChangeView):
    template_name = "accounts/change_password.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        messages.success(self.request, "Đã đổi mật khẩu thành công.")
        return super().form_valid(form)
