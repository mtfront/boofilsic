from django import forms
from .models import Report
from django.utils.translation import gettext_lazy as _


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = [
            'reported_user',
            'image',
            'message',
        ]
        widgets = {
            'message': forms.Textarea(attrs={'placeholder': _("详情")}),
        } 
        labels = {
            'reported_user': _("举报的用户"),
            'image':  _("相关证据"),
            'message': _("详情")
        }