from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import DailyCheckin, MITSession, Skill


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-control"}))

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})


class DailyCheckinForm(forms.ModelForm):
    class Meta:
        model = DailyCheckin
        fields = ["date", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Optional notes..."}),
        }


class FocusCategoryForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ["name", "description", "weekly_goal_minutes", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Autodesk Fusion"}),
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional short description"}),
            "weekly_goal_minutes": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class MITSessionForm(forms.ModelForm):
    completed = forms.BooleanField(label="Completed", required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))

    class Meta:
        model = MITSession
        fields = ["skill", "actual_minutes"]
        widgets = {
            "skill": forms.Select(attrs={"class": "form-select"}),
            "actual_minutes": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        qs = Skill.objects.filter(is_active=True)
        if user and user.is_authenticated:
            qs = qs.filter(owner=user)
        self.fields["skill"].queryset = qs
        self.fields["skill"].required = True
        self.fields["actual_minutes"].label = "Minutes"
        self.fields["actual_minutes"].required = True
        self.fields["actual_minutes"].widget.attrs.update({"min": 1})
        self.fields["completed"].initial = self.instance.status == MITSession.Status.COMPLETED if self.instance.pk else False

    def clean_actual_minutes(self):
        minutes = self.cleaned_data.get("actual_minutes")
        if not minutes or minutes <= 0:
            raise forms.ValidationError("Log at least 1 minute.")
        return minutes

    def save(self, commit=True):
        instance = super().save(commit=False)
        minutes = self.cleaned_data.get("actual_minutes") or 0
        completed = self.cleaned_data.get("completed")
        instance.planned_minutes = minutes
        if completed:
            instance.actual_minutes = minutes
            instance.status = MITSession.Status.COMPLETED
        else:
            instance.actual_minutes = None
            instance.status = MITSession.Status.PLANNED
        if not instance.title:
            skill = self.cleaned_data.get("skill") or instance.skill
            instance.title = skill.name if skill else "Focus Session"
        if commit:
            instance.save()
        return instance


class BaseMITSessionInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        valid_forms = [f for f in self.forms if f.cleaned_data and not f.cleaned_data.get("DELETE", False)]
        if len(valid_forms) < 1:
            raise forms.ValidationError("Add at least 1 MIT entry.")

        for form in valid_forms:
            skill = form.cleaned_data.get("skill")
            minutes = form.cleaned_data.get("actual_minutes")

            if not skill:
                raise forms.ValidationError("Choose a focus category for each Focus Session.")
            if not minutes or minutes <= 0:
                raise forms.ValidationError("Log at least 1 minute for every Focus Session.")


MITSessionFormSet = inlineformset_factory(
    DailyCheckin,
    MITSession,
    form=MITSessionForm,
    formset=BaseMITSessionInlineFormSet,
    extra=1,
    min_num=1,
    max_num=8,
    validate_min=True,
    validate_max=True,
    can_delete=True,
)
