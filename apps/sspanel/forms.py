from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm

from apps.ext import encoder
from apps.sspanel.models import (
    Announcement,
    Goods,
    InviteCode,
    User,
    SSNode,
    VmessNode,
    UserSSConfig,
)


class RegisterForm(UserCreationForm):
    """注册时渲染的表单"""

    username = forms.CharField(
        label="用户名",
        help_text="必填。150个字符或者更少。包含字母，数字和仅有的@/./+/-/_符号。",
        widget=forms.TextInput(attrs={"class": "input is-info"}),
    )

    email = forms.EmailField(
        label="邮箱", widget=forms.TextInput(attrs={"class": "input is-warning"})
    )
    password1 = forms.CharField(
        label="密码",
        help_text="""你的密码不能与其他个人信息太相似。
                                                        你的密码必须包含至少 8 个字符。
                                                        你的密码不能是大家都爱用的常见密码
                                                        你的密码不能全部为数字。""",
        widget=forms.TextInput(attrs={"class": "input is-primary", "type": "password"}),
    )
    password2 = forms.CharField(
        label="重复密码",
        widget=forms.TextInput(attrs={"class": "input is-danger", "type": "password"}),
    )

    invitecode = forms.CharField(
        label="邀请码",
        help_text="邀请码必须填写",
        widget=forms.TextInput(attrs={"class": "input is-success"}),
    )

    ref = forms.CharField(
        label="邀请", widget=forms.TextInput(attrs={"class": "input is-success"})
    )

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        if "ref" in self.data or "ref" in self.initial.keys():
            self.fields.pop("invitecode")
        else:
            self.fields.pop("ref")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).first():
            raise forms.ValidationError("该邮箱已经注册过了")
        else:
            return email

    def _post_clean(self):
        super()._post_clean()
        if "ref" in self.fields:
            try:
                self._clean_ref()
            except forms.ValidationError as error:
                self.add_error("ref", error)
        if "invitecode" in self.fields:
            try:
                self._clean_invitecode()
            except forms.ValidationError as error:
                self.add_error("invitecode", error)

    def _clean_invitecode(self):
        code = self.cleaned_data.get("invitecode")
        if InviteCode.objects.filter(code=code, used=False).exists():
            return code
        else:
            raise forms.ValidationError("该邀请码失效")

    def _clean_ref(self):
        ref = self.cleaned_data.get("ref")
        try:
            user_id = encoder.string2int(ref)
        except ValueError:
            raise forms.ValidationError("ref不正确")

        if User.objects.filter(id=user_id).exists():
            return ref
        else:
            raise forms.ValidationError("ref不正确")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2", "invitecode", "ref")


class LoginForm(forms.Form):
    username = forms.CharField(
        required=True,
        label=u"用户名",
        error_messages={"required": "请输入用户名"},
        widget=forms.TextInput(
            attrs={"class": "input is-primary", "placeholder": "用户名"}
        ),
    )
    password = forms.CharField(
        required=True,
        label=u"密码",
        error_messages={"required": u"请输入密码"},
        widget=forms.PasswordInput(
            attrs={"class": "input is-primary", "placeholder": "密码", "type": "password"}
        ),
    )

    def clean(self):
        if not self.is_valid():
            raise forms.ValidationError(u"用户名和密码为必填项")
        else:
            self.cleaned_data = super(LoginForm, self).clean()


class SSNodeForm(ModelForm):
    class Meta:
        model = SSNode
        fields = "__all__"
        widgets = {
            "node_id": forms.NumberInput(attrs={"class": "input"}),
            "level": forms.NumberInput(attrs={"class": "input"}),
            "enlarge_scale": forms.NumberInput(attrs={"class": "input"}),
            "name": forms.TextInput(attrs={"class": "input"}),
            "info": forms.TextInput(attrs={"class": "input"}),
            "server": forms.TextInput(attrs={"class": "input"}),
            "method": forms.Select(attrs={"class": "input"}),
            "country": forms.Select(attrs={"class": "input"}),
            "used_traffic": forms.NumberInput(attrs={"class": "input"}),
            "total_traffic": forms.NumberInput(attrs={"class": "input"}),
            "enable": forms.CheckboxInput(attrs={"class": "checkbox"}),
            "custom_method": forms.CheckboxInput(attrs={"class": "checkbox"}),
            "speed_limit": forms.NumberInput(attrs={"class": "input"}),
        }


class VmessNodeForm(ModelForm):
    class Meta:
        model = VmessNode
        fields = "__all__"
        widgets = {
            "node_id": forms.NumberInput(attrs={"class": "input"}),
            "level": forms.NumberInput(attrs={"class": "input"}),
            "enlarge_scale": forms.NumberInput(attrs={"class": "input"}),
            "name": forms.TextInput(attrs={"class": "input"}),
            "inbound_tag": forms.TextInput(attrs={"class": "input"}),
            "alter_id": forms.NumberInput(attrs={"class": "input"}),
            "port": forms.NumberInput(attrs={"class": "input"}),
            "offset_port": forms.NumberInput(attrs={"class": "input"}),
            "info": forms.TextInput(attrs={"class": "input"}),
            "server": forms.TextInput(attrs={"class": "input"}),
            "grpc_host": forms.TextInput(attrs={"class": "input"}),
            "grpc_port": forms.TextInput(attrs={"class": "input"}),
            "country": forms.Select(attrs={"class": "input"}),
            "used_traffic": forms.NumberInput(attrs={"class": "input"}),
            "total_traffic": forms.NumberInput(attrs={"class": "input"}),
            "enable": forms.CheckboxInput(attrs={"class": "checkbox"}),
            "relay_host": forms.TextInput(attrs={"class": "input"}),
            "relay_port": forms.TextInput(attrs={"class": "input"}),
            "relay_offset_port": forms.TextInput(attrs={"class": "input"}),
        }


class GoodsForm(ModelForm):
    class Meta:
        model = Goods
        fields = "__all__"


class AnnoForm(ModelForm):
    class Meta:
        model = Announcement
        fields = "__all__"


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ["balance", "level", "level_expire_time"]
        widgets = {
            "balance": forms.NumberInput(attrs={"class": "input"}),
            "level": forms.NumberInput(attrs={"class": "input"}),
            "level_expire_time": forms.DateTimeInput(attrs={"class": "input"}),
        }


class UserSSConfigForm(ModelForm):
    class Meta:
        model = UserSSConfig
        fields = ["port", "password", "method"]
        widgets = {
            "port": forms.NumberInput(attrs={"class": "input"}),
            "password": forms.TextInput(attrs={"class": "input"}),
            "method": forms.Select(attrs={"class": "input"}),
        }
