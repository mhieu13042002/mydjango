from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings
import os

from .models import Expense, Category


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["title", "type", "category", "amount", "date", "note"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "VD: Ăn trưa quán cơm"}),
            "type": forms.Select(attrs={"class": "form-select"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": 1000}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["category"].queryset = Category.objects.filter(
                models_q(user)
            ).order_by("type", "name")

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise ValidationError("Số tiền phải lớn hơn 0.")
        return amount


def models_q(user):
    from django.db.models import Q
    return Q(user=user) | Q(user__isnull=True)


class ExpenseImageUploadForm(forms.Form):
    image = forms.ImageField()

    def clean_image(self):
        image = self.cleaned_data["image"]
        ext = os.path.splitext(image.name)[1].lower()
        if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationError("Chỉ chấp nhận ảnh định dạng JPG, PNG hoặc WEBP.")
        if image.size > settings.MAX_IMAGE_SIZE_MB * 1024 * 1024:
            raise ValidationError(f"Ảnh không được vượt quá {settings.MAX_IMAGE_SIZE_MB}MB.")
        return image
