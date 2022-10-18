import pendulum
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.ext import lock
from apps.proxy import models as m
from apps.sspanel import tasks
from apps.sspanel.models import Goods, User, UserCheckInLog, UserOrder
from apps.sub import UserSubManager
from apps.tianyi import DashBoardManger
from apps.utils import (
    api_authorized,
    gen_datetime_list,
    get_client_ip,
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
        if success := request.user.update_ss_config_from_dict(
            data=dict(request.POST.items())
        ):
            data = {"title": "修改成功!", "status": "success", "subtitle": "请及时更换客户端配置!"}
        else:
            data = {"title": "修改失败!", "status": "error", "subtitle": "配置更新失败!"}
        return JsonResponse(data)


class SubscribeView(View):
    def get(self, request):
        user = None
        if uid := request.GET.get("uid"):
            user = User.objects.filter(uid=uid).first()
        if not user:
            return HttpResponseBadRequest("user not found")
        node_list = m.ProxyNode.get_active_nodes(level=user.level)

        if protocol := request.GET.get("protocol"):
            node_list = node_list.filter(node_type=protocol)

        if len(node_list) == 0:
            return HttpResponseBadRequest("no active nodes for you")

        sub_client = request.GET.get("client")

        sub_type = request.GET.get("sub_type")
        if not sub_client:
            # todo delete this workaround
            SUB_TYPE_SS = "ss"
            SUB_TYPE_CLASH = "clash"
            SUB_TYPE_CLASH_PRO = "clash_pro"
            if sub_type == SUB_TYPE_SS:
                sub_client = UserSubManager.CLIENT_SHADOWROCKET
            elif sub_type == SUB_TYPE_CLASH:
                sub_client = UserSubManager.CLIENT_CLASH
            elif sub_type == SUB_TYPE_CLASH_PRO:
                sub_client = UserSubManager.CLIENT_CLASH_PREMIUM
        # end todo

        sub_info = UserSubManager(user, sub_client, node_list).get_sub_info()
        return HttpResponse(
            sub_info,
            content_type="text/plain; charset=utf-8",
            headers=user.get_subinfo_header(),
        )


class ClashProxyProviderView(View):
    def get(self, request):
        user = None
        if uid := request.GET.get("uid"):
            user = User.objects.filter(uid=uid).first()
        if not user:
            return HttpResponseBadRequest("user not found")
        node_list = m.ProxyNode.get_active_nodes(level=user.level)
        if len(node_list) == 0:
            return HttpResponseBadRequest("no active nodes for you")

        providers = UserSubManager(
            user, request.GET.get("sub_type"), node_list
        ).get_clash_proxy_providers()

        return HttpResponse(
            providers,
            content_type="text/plain; charset=utf-8",
        )


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
        return (
            JsonResponse(node.get_proxy_configs()) if node else HttpResponseBadRequest()
        )

    @method_decorator(handle_json_post)
    @method_decorator(api_authorized)
    def post(self, request, node_id):
        node = m.ProxyNode.get_or_none(node_id)
        if not node:
            return HttpResponseBadRequest()
        tasks.sync_user_traffic_task.delay(node_id, request.json["data"])
        return JsonResponse(data={})


class EhcoRelayConfigView(View):
    """中转机器"""

    @method_decorator(api_authorized)
    def get(self, request, node_id):
        node: m.RelayNode = m.RelayNode.get_or_none(node_id)
        return (
            JsonResponse(node.get_relay_rules_configs())
            if node
            else HttpResponseBadRequest()
        )


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
            if amount < 1:
                raise ValueError
        except ValueError:
            return JsonResponse(
                {"info": {"title": "校验失败", "subtitle": "请保证金额正确", "status": "error"}},
            )

        if settings.CHECK_PAY_REQ_IP_FROM_CN:
            from ipicn import is_in_china

            if not is_in_china(get_client_ip(request)):
                return JsonResponse(
                    {
                        "info": {
                            "title": "校验失败",
                            "subtitle": "支付时请不要使用代理软件",
                            "status": "error",
                        }
                    }
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
@require_http_methods(["POST"])
def purchase(request):
    good_id = request.POST.get("goodId")
    good = Goods.objects.get(id=good_id)
    return (
        JsonResponse({"title": "购买成功", "status": "success", "subtitle": "重新订阅即可获取所有节点"})
        if good.purchase_by_user(request.user)
        else JsonResponse({"title": "余额不足", "status": "error", "subtitle": "先去捐赠充值那充值"})
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


@login_required
def reset_sub_uid(request):
    """
    更换用户订阅 uid
    """
    user = request.user
    user.reset_sub_uid()
    res = {"title": "修改成功！", "subtitle": "订阅更换成功，刷新页面可见", "status": "success"}
    return JsonResponse(res)


@csrf_exempt
@require_http_methods(["POST"])
def ailpay_callback(request):
    data = request.POST.dict()
    if success := UserOrder.handle_callback_by_alipay(data):
        return HttpResponse("success")
    else:
        return HttpResponse("failure")
