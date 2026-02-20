from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import DailyCheckin, MITSession


class DailyCheckinForm(forms.ModelForm):
    class Meta:
        model = DailyCheckin
        fields = ["date", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Optional notes..."}),
        }


class MITSessionForm(forms.ModelForm):
    class Meta:
        model = MITSession
        fields = ["category", "title", "planned_minutes", "actual_minutes", "status"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "What will you do?"}),
            "planned_minutes": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "actual_minutes": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class BaseMITSessionInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        valid_forms = [f for f in self.forms if f.cleaned_data and not f.cleaned_data.get("DELETE", False)]
        if len(valid_forms) != 3:
            raise forms.ValidationError("Please enter exactly 3 MITs.")

        categories = [f.cleaned_data.get("category") for f in valid_forms]
        expected = {MITSession.Category.BIBLE, MITSession.Category.GUITAR, MITSession.Category.WORK_SKILL}
        if set(categories) != expected:
            raise forms.ValidationError("You must include one each: Bible, Guitar, and Work/Skill.")


MITSessionFormSet = inlineformset_factory(
    DailyCheckin,
    MITSession,
    form=MITSessionForm,
    formset=BaseMITSessionInlineFormSet,
    extra=3,
    min_num=3,
    max_num=3,
    validate_min=True,
    validate_max=True,
    can_delete=False,
)
