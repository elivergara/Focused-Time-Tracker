from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import DailyCheckin, MITSession, Skill


class DailyCheckinForm(forms.ModelForm):
    class Meta:
        model = DailyCheckin
        fields = ["date", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Optional notes..."}),
        }


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ["name", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Autodesk Fusion"}),
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional short description"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class MITSessionForm(forms.ModelForm):
    class Meta:
        model = MITSession
        fields = ["category", "skill", "title", "planned_minutes", "actual_minutes", "status", "miss_reason"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "skill": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "What will you do?"}),
            "planned_minutes": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "actual_minutes": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "miss_reason": forms.TextInput(attrs={"class": "form-control", "placeholder": "If skipped, why?"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["skill"].queryset = Skill.objects.filter(is_active=True)
        self.fields["skill"].required = False
        self.fields["miss_reason"].required = False


class BaseMITSessionInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        valid_forms = [f for f in self.forms if f.cleaned_data and not f.cleaned_data.get("DELETE", False)]
        if len(valid_forms) != 3:
            raise forms.ValidationError("Please enter exactly 3 MITs.")

        categories = [f.cleaned_data.get("category") for f in valid_forms]
        if MITSession.Category.BIBLE not in categories or MITSession.Category.GUITAR not in categories:
            raise forms.ValidationError("You must include Bible and Guitar MITs.")
        if not any(c in {MITSession.Category.WORK_SKILL, MITSession.Category.CUSTOM_SKILL} for c in categories):
            raise forms.ValidationError("The third MIT must be Work/Skill or Custom Skill.")

        for form in valid_forms:
            category = form.cleaned_data.get("category")
            skill = form.cleaned_data.get("skill")
            status = form.cleaned_data.get("status")
            miss_reason = (form.cleaned_data.get("miss_reason") or "").strip()

            if category == MITSession.Category.CUSTOM_SKILL and not skill:
                raise forms.ValidationError("Select a skill when category is Custom Skill.")
            if status == MITSession.Status.SKIPPED and not miss_reason:
                raise forms.ValidationError("Add a miss reason for any skipped MIT.")


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
