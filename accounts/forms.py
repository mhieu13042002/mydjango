from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(
        attrs={"class": "form-control", "placeholder": "email@example.com"}))
    first_name = forms.CharField(required=True, max_length=30, widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "Họ và tên"}))

    class Meta:
        model = User
        fields = ["username", "first_name", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control", "placeholder": "Tên đăng nhập"})
        self.fields["password1"].widget.attrs.update({"class": "form-control", "placeholder": "Mật khẩu"})
        self.fields["password2"].widget.attrs.update({"class": "form-control", "placeholder": "Nhập lại mật khẩu"})

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email này đã được sử dụng.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-control"}))

    class Meta:
        model = Profile
        fields = ["phone", "avatar", "monthly_income_estimate"]
        widgets = {
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Số điện thoại"}),
            "avatar": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "monthly_income_estimate": forms.NumberInput(attrs={"class": "form-control"}),
        }
