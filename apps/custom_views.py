from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetView
from django.core.paginator import EmptyPage, Paginator
from django.template import loader

from apps.sspanel.models import User
from apps.sspanel.tasks import send_mail_to_users_task


class AsyncPasswordResetForm(PasswordResetForm):
    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """
        Copy and adapted from django.contrib.auth.forms.PasswordResetForm
        """
        subject = loader.render_to_string(subject_template_name, context)
        subject = "".join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)
        user = User.objects.get(email=to_email)
        send_mail_to_users_task.delay([user.id], subject, body)


class AsyncPasswordResetView(PasswordResetView):
    form_class = AsyncPasswordResetForm


class PageListView:
    """
    拥有翻页功能的通用类
    Args:
        request ： django request
        obj_list： 等待分分页的列表
        page_num： 分页的页数
    """

    def __init__(self, request, obj_list, page_num=10):
        self.request = request
        self.obj_list = obj_list
        self.page_num = page_num

    def get_page_context(self):
        """返回分页context"""
        # 每页显示10条记录
        paginator = Paginator(self.obj_list, self.page_num)
        # 构造分页.获取当前页码数量
        page = int(self.request.GET.get("page", 1))
        # 页码为1时，防止异常
        try:
            contacts = paginator.page(page)
        except EmptyPage:
            contacts = paginator.page(paginator.num_pages)
        # 获得整个分页页码列表
        page_list = paginator.page_range
        # 获得分页后的总页数
        total = paginator.num_pages

        left = []
        left_has_more = False
        right = []
        right_has_more = False
        first = False
        last = False
        # 开始构造页码列表
        if page == 1:
            # 当前页为第1页时
            right = page_list[page : page + 2]
            if len(right) > 0:
                # 当最后一页比总页数小时，我们应该显示省略号
                if right[-1] < total - 1:
                    right_has_more = True
                # 当最后一页比right大时候，我们需要显示最后一页
                if right[-1] < total:
                    last = True
        elif page >= total:
            # 当前页为最后一页时
            left = page_list[page - 3 if page > 3 else 0 : page - 1]
            if len(left) > 0 and left[0] > 2:
                left_has_more = True
            if len(left) > 0 and left[0] > 1:
                first = True
        else:
            left = page_list[page - 2 if page > 2 else 0 : page - 1]
            right = page_list[page : page + 2]
            # 是否需要显示最后一页和最后一页前的省略号
            if len(right) > 0 and right[-1] < total - 1:
                right_has_more = True
            if len(right) > 0 and right[-1] < total:
                last = True
            # 是否需要显示第 1 页和第 1 页后的省略号
            if len(left) > 0 and left[0] > 2:
                left_has_more = True
            if len(left) > 0 and left[0] > 1:
                first = True
        return {
            "contacts": contacts,
            "page_list": page_list,
            "left": left,
            "right": right,
            "left_has_more": left_has_more,
            "right_has_more": right_has_more,
            "first": first,
            "last": last,
            "total": total,
            "page": page,
        }
