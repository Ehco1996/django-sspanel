from django import forms
from django.contrib.auth.forms import AuthenticationForm as auth_login_form
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm

from .models import Announcement, Shop, User
from ssserver.models import Node


class RegisterForm(UserCreationForm):
    '''注册时渲染的表单'''

    username = forms.CharField(label='用户名', help_text='必填。150个字符或者更少。包含字母，数字和仅有的@/./+/-/_符号。',
                               widget=forms.TextInput(
                                   attrs={'class': 'input is-info'})
                               )

    email = forms.EmailField(label='邮箱',
                             widget=forms.TextInput(
                                 attrs={'class': 'input is-warning'})
                             )
    invitecode = forms.CharField(label='邀请码', help_text='邀请码必须填写',
                                 widget=forms.TextInput(
                                     attrs={'class': 'input is-success'})
                                 )
    password1 = forms.CharField(label='密码', help_text='''你的密码不能与其他个人信息太相似。
                                                        你的密码必须包含至少 8 个字符。
                                                        你的密码不能是大家都爱用的常见密码
                                                        你的密码不能全部为数字。''',
                                widget=forms.TextInput(
                                    attrs={'class': 'input is-primary', 'type': 'password'})
                                )
    password2 = forms.CharField(label='重复密码',
                                widget=forms.TextInput(
                                    attrs={'class': 'input is-danger', 'type': 'password'})
                                )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        t = User.objects.filter(email=email)
        if len(t) != 0:
            raise forms.ValidationError('该邮箱已经注册过了')
        else:
            return email

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'invitecode',)


class LoginForm(forms.Form):
    username = forms.CharField(
        required=True,
        label=u"用户名",
        error_messages={'required': '请输入用户名'},
        widget=forms.TextInput(
            attrs={
                'class': 'input is-primary',
                'placeholder': "用户名",
            }
        ),
    )
    password = forms.CharField(
        required=True,
        label=u"密码",
        error_messages={'required': u'请输入密码'},
        widget=forms.PasswordInput(
            attrs={
                'class': 'input is-primary',
                'placeholder': "密码",
                'type': 'password',
            }
        ),
    )

    def clean(self):
        if not self.is_valid():
            raise forms.ValidationError(u"用户名和密码为必填项")
        else:
            cleaned_data = super(LoginForm, self).clean()


class NodeForm(ModelForm):
    class Meta:
        model = Node
        fields = '__all__'
        exclude=['total_traffic','used_traffic','human_used_traffic']

class ShopForm(ModelForm):
    class Meta:
        model = Shop
        fields = '__all__'


class AnnoForm(ModelForm):
    class Meta:
        model = Announcement
        fields = '__all__'


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['balance', 'level', 'level_expire_time', ]
        widgets = {
            'balance': forms.NumberInput(attrs={'class': 'input'}),
            'level': forms.NumberInput(attrs={'class': 'input'}),
            'level_expire_time': forms.DateTimeInput(attrs={'class': 'input'}),
        }
