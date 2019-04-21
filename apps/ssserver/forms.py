from django import forms
from django.forms import ModelForm
from .models import Suser


class SuserForm(ModelForm):
    class Meta:
        model = Suser
        fields = [
            "port",
            "password",
            "upload_traffic",
            "download_traffic",
            "transfer_enable",
            "enable",
        ]
        widgets = {
            "enable": forms.CheckboxInput(attrs={"class": "checkbox"}),
            "port": forms.NumberInput(attrs={"class": "input"}),
            "password": forms.TextInput(attrs={"class": "input"}),
            "upload_traffic": forms.NumberInput(attrs={"class": "input"}),
            "download_traffic": forms.NumberInput(attrs={"class": "input"}),
            "transfer_enable": forms.NumberInput(attrs={"class": "input"}),
        }
