from django import forms
from .models import SSUser


class ChangeSsPassForm(forms.Form):

    password = forms.CharField(
        required=True,
        label="连接密码",
        error_messages={'required': '请输入密码'},
        widget=forms.PasswordInput(
            attrs={
                'class': 'input is-danger',
                'placeholder': "密码",
                'type': 'text',
            }
        ),
    )

    def clean(self):
        if not self.is_valid():
            raise forms.ValidationError('太短啦！')
        else:
            cleaned_data = super(ChangeSsPassForm, self).clean()
