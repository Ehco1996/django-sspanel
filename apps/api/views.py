import pendulum
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.ext import encoder, lock
from apps.proxy import models as m
from apps.sspanel import tasks
from apps.sspanel.models import Goods, InviteCode, User, UserCheckInLog, UserOrder
from apps.sub import UserSubManager
from apps.tianyi import DashBoardManger
from apps.utils import (
    api_authorized,
    gen_datetime_list,
    get_current_datetime,
    handle_json_post,
    traffic_format,
)


class SystemStatusView(View):
    @method_decorator(permission_required("sspanel"))
    def get(self, request):
        start = pendulum.parse(request.GET["start"])
        end = pendulum.parse(request.GET["end"])
        dt_list = [start.add(days=i) for i in range((end - start).days + 1)]
        dm = DashBoardManger(dt_list)
        data = {
            "node_status": dm.get_node_status(),
            "user_status": dm.get_user_status_data(),
            "order_status": dm.get_userorder_status_data(),
        }
        return JsonResponse(data)


class UserSettingsView(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(UserSettingsView, self).dispatch(*args, **kwargs)

    @method_decorator(login_required)
    def post(self, request):
        success = request.user.update_ss_config_from_dict(
            data={k: v for k, v in request.POST.items()}
        )
        if success:
            data = {"title": "修改成功!", "status": "success", "subtitle": "请及时更换客户端配置!"}
        else:
            data = {"title": "修改失败!", "status": "error", "subtitle": "配置更新失败!"}
        return JsonResponse(data)


class SubscribeView(View):
    def get(self, request):
        token = request.GET.get("token")
        if not token:
            return HttpResponseNotFound()
        user = User.get_or_none(encoder.string2int(token))
        if not user:
            return HttpResponseNotFound()

        sub_type = request.GET.get("sub_type")
        sub_links = UserSubManager(user, sub_type, request).get_sub_links()
        return HttpResponse(sub_links, content_type="text/plain; charset=utf-8")


class UserRefChartView(View):
    @method_decorator(login_required)
    def get(self, request):
        date = request.GET.get("date")
        t = pendulum.parse(date) if date else get_current_datetime()
        bar_configs = DashBoardManger.gen_ref_log_bar_chart_configs(
            request.user.id, [dt.date() for dt in gen_datetime_list(t)]
        )
        return JsonResponse(bar_configs)


class UserTrafficChartView(View):
    @method_decorator(login_required)
    def get(self, request):
        node_id = request.GET.get("node_id", 0)
        user_id = request.user.pk
        configs = DashBoardManger.gen_traffic_line_chart_configs(
            user_id, node_id, gen_datetime_list(get_current_datetime())
        )
        return JsonResponse(configs)


class ProxyConfigsView(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(ProxyConfigsView, self).dispatch(*args, **kwargs)

    @method_decorator(api_authorized)
    def get(self, request, node_id):
        node = m.ProxyNode.get_or_none(node_id)
        if not node:
            return HttpResponseNotFound()
        return JsonResponse(node.get_proxy_configs())

    @method_decorator(handle_json_post)
    @method_decorator(api_authorized)
    def post(self, request, node_id):
        node = m.ProxyNode.get_or_none(node_id)
        if not node:
            return HttpResponseNotFound()
        tasks.sync_user_traffic_task.delay(node_id, request.json["data"])
        return JsonResponse(data={})


class EhcoRelayConfigView(View):
    """中转机器"""

    @method_decorator(api_authorized)
    def get(self, request, node_id):
        node = m.RelayNode.get_or_none(node_id)
        if not node:
            return HttpResponseNotFound()
        return JsonResponse(node.get_relay_rules_configs())


class EhcoServerConfigView(View):
    """落地机器"""

    @method_decorator(api_authorized)
    def get(self, request, node_id):
        node = m.ProxyNode.get_or_none(node_id)
        if not node:
            return HttpResponseNotFound()
        return JsonResponse(node.get_ehco_server_config())


class UserCheckInView(View):
    @method_decorator(login_required)
    def post(self, request):
        user = request.user
        with lock.user_checkin_lock(user.pk):
            if not user.today_is_checkin:
                log = UserCheckInLog.checkin(user)
                data = {
                    "title": "签到成功！",
                    "subtitle": f"获得{traffic_format(log.increased_traffic)}流量！",
                    "status": "success",
                }
            else:
                data = {"title": "签到失败！", "subtitle": "今天已经签到过了", "status": "error"}
        return JsonResponse(data)


class ReSetSSPortView(View):
    @method_decorator(login_required)
    def post(self, request):
        port = request.user.reset_random_port()
        data = {
            "title": "修改成功！",
            "subtitle": "端口修改为：{}！".format(port),
            "status": "success",
        }
        return JsonResponse(data)


class OrderView(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        order = UserOrder.get_and_check_recent_created_order(user)
        if order and order.status != UserOrder.STATUS_CREATED:
            info = {"title": "充值成功!", "subtitle": "请去商品界面购买商品！", "status": "success"}
        else:
            info = {"title": "支付查询失败!", "subtitle": "亲，确认支付了么？", "status": "error"}
        return JsonResponse({"info": info})

    @method_decorator(login_required)
    def post(self, request):
        try:
            amount = int(request.POST.get("num"))
            if amount < 1 or amount > 99999:
                raise ValueError
        except ValueError:
            return JsonResponse(
                {"info": {"title": "失败", "subtitle": "请保证金额正确", "status": "error"}},
            )
        order = UserOrder.get_or_create_order(request.user, amount)
        info = {
            "title": "请求成功！",
            "subtitle": "支付宝扫描下方二维码付款，付款完成记得按确认哟！",
            "status": "success",
        }
        return JsonResponse(
            {"info": info, "qrcode_url": order.qrcode_url, "order_id": order.id}
        )


@login_required
def gen_invite_code(request):
    """
    生成用户的邀请码
    返回是否成功
    """
    num = InviteCode.create_by_user(request.user)
    if num > 0:
        registerinfo = {
            "title": "成功",
            "subtitle": "添加邀请码{}个,请刷新页面".format(num),
            "status": "success",
        }
    else:
        registerinfo = {"title": "失败", "subtitle": "已经不能生成更多的邀请码了", "status": "error"}
    return JsonResponse(registerinfo)


@login_required
@require_http_methods(["POST"])
def purchase(request):
    good_id = request.POST.get("goodId")
    good = Goods.objects.get(id=good_id)
    if not good.purchase_by_user(request.user):
        return JsonResponse(
            {"title": "余额不足", "status": "error", "subtitle": "请去捐赠充值界面充值哦"}
        )
    else:
        return JsonResponse(
            {"title": "购买成功", "status": "success", "subtitle": "请在用户中心检查最新信息"}
        )


@login_required
def change_theme(request):
    """
    更换用户主题
    """
    theme = request.POST.get("theme", "default")
    user = request.user
    user.theme = theme
    user.save()
    res = {"title": "修改成功！", "subtitle": "主题更换成功，刷新页面可见", "status": "success"}
    return JsonResponse(res)


@csrf_exempt
@require_http_methods(["POST"])
def ailpay_callback(request):
    data = request.POST.dict()
    success = UserOrder.handle_callback_by_alipay(data)
    if success:
        return HttpResponse("success")
    else:
        return HttpResponse("failure")
