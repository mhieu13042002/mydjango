from django import forms
from core.forms import VNDAmountField
from .models import SavingGoal, GoalContribution

MONEY_ATTRS = {
    "class": "form-control js-money-input", "inputmode": "numeric",
    "autocomplete": "off", "placeholder": "0",
}


class SavingGoalForm(forms.ModelForm):
    class Meta:
        model = SavingGoal
        fields = ["name", "target_amount", "deadline", "icon"]
        field_classes = {"target_amount": VNDAmountField}
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "VD: Mua laptop mới"}),
            "target_amount": forms.TextInput(attrs=MONEY_ATTRS),
            "deadline": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "icon": forms.TextInput(attrs={"class": "form-control", "placeholder": "🎯"}),
        }


class GoalContributionForm(forms.ModelForm):
    class Meta:
        model = GoalContribution
        fields = ["amount", "date", "note"]
        field_classes = {"amount": VNDAmountField}
        widgets = {
            "amount": forms.TextInput(attrs=MONEY_ATTRS),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "note": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ghi chú (không bắt buộc)"}),
        }
