from brabbl.core.models import Discussion
from django import forms
from django.utils.translation import ugettext_lazy as _


class DiscussionForm(forms.ModelForm):
    class Meta:
        model = Discussion
        fields = "__all__"

    def clean(self):
        cleaned_data = super(DiscussionForm, self).clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time:
            if end_time < start_time:
                raise forms.ValidationError(_("End time cannot be earlier than start time!"))
        return cleaned_data
