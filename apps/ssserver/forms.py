from django import forms
from django.forms import ModelForm
from .models import Suser


class ChangeSsPassForm(forms.Form):

    password = forms.CharField(
        required=True,
        label="连接密码",
        error_messages={"required": "请输入密码"},
        widget=forms.PasswordInput(
            attrs={"class": "input is-danger", "placeholder": "密码", "type": "text"}
        ),
    )

    def clean(self):
        if not self.is_valid():
            raise forms.ValidationError("太短啦！")
        else:
            self.cleaned_data = super(ChangeSsPassForm, self).clean()


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
