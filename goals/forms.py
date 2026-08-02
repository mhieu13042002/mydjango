from django import forms
from .models import SavingGoal, GoalContribution


class SavingGoalForm(forms.ModelForm):
    class Meta:
        model = SavingGoal
        fields = ["name", "target_amount", "deadline", "icon"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "VD: Mua laptop mới"}),
            "target_amount": forms.NumberInput(attrs={"class": "form-control", "min": 1000, "step": 1000}),
            "deadline": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "icon": forms.TextInput(attrs={"class": "form-control", "placeholder": "🎯"}),
        }


class GoalContributionForm(forms.ModelForm):
    class Meta:
        model = GoalContribution
        fields = ["amount", "date", "note"]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control", "min": 1000, "step": 1000}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "note": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ghi chú (không bắt buộc)"}),
        }
