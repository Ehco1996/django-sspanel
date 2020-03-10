import pendulum
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.ext import encoder
from apps.sspanel.models import (
    Donate,
    Goods,
    InviteCode,
    NodeOnlineLog,
    SSNode,
    User,
    UserCheckInLog,
    UserOnLineIpLog,
    UserOrder,
    UserRefLog,
    UserTrafficLog,
    VmessNode,
)
from apps.utils import api_authorized, handle_json_post, traffic_format


class SystemStatusView(View):
    @method_decorator(permission_required("sspanel"))
    def get(self, request):
        user_status = [
            NodeOnlineLog.get_all_node_online_user_count(),
            User.get_today_register_user().count(),
            UserCheckInLog.get_today_checkin_user_count(),
            User.get_never_used_user_count(),
        ]
        donate_status = [
            Donate.get_donate_count_by_date(),
            Donate.get_donate_money_by_date(),
            Donate.get_donate_count_by_date(date=pendulum.today()),
            Donate.get_donate_money_by_date(date=pendulum.today()),
        ]

        active_nodes = SSNode.get_active_nodes() + VmessNode.get_active_nodes()

        node_status = {
            "names": [node.name for node in active_nodes],
            "traffics": [
                round(node.used_traffic / settings.GB, 2) for node in active_nodes
            ],
        }
        data = {
            "user_status": user_status,
            "donate_status": donate_status,
            "node_status": node_status,
        }
        return JsonResponse(data)


class UserSettingsView(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(UserSettingsView, self).dispatch(*args, **kwargs)

    @method_decorator(login_required)
    def post(self, request):
        success = request.user.update_from_dict(
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
        sub_links = user.get_sub_links(sub_type)
        return HttpResponse(sub_links)


class UserRefChartView(View):
    @method_decorator(login_required)
    def get(self, request):
        # 最近10天的
        date = request.GET.get("date")
        t = pendulum.parse(date) if date else pendulum.now()
        date_list = [t.add(days=i).date() for i in range(-7, 3)]
        bar_configs = UserRefLog.gen_bar_chart_configs(request.user.id, date_list)
        return JsonResponse(bar_configs)


class UserTrafficChartView(View):
    @method_decorator(login_required)
    def get(self, request):
        node_id = request.GET.get("node_id", 0)
        node_type = request.GET.get("node_type", "ss")
        user_id = request.user.pk
        now = pendulum.now()
        last_week = [now.subtract(days=i).date() for i in range(6, -1, -1)]
        configs = UserTrafficLog.gen_line_chart_configs(
            user_id, node_type, node_id, last_week
        )
        return JsonResponse(configs)


class UserSSConfigView(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(UserSSConfigView, self).dispatch(*args, **kwargs)

    @method_decorator(api_authorized)
    def get(self, request, node_id):
        configs = SSNode.get_user_ss_configs_by_node_id(node_id)
        return JsonResponse(configs)

    @method_decorator(handle_json_post)
    @method_decorator(api_authorized)
    def post(self, request, node_id):
        """
        这个接口操作比较重，所以为了避免发信号
        所有写操作都需要用BULK的方式
        1 更新节点流量
        2 更新用户流量
        3 记录节点在线IP
        4 关闭超出流量的节点
        """
        ss_node = SSNode.get_or_none_by_node_id(node_id)
        if not ss_node:
            return HttpResponseNotFound()

        data = request.json["data"]
        node_total_traffic = 0
        log_time = pendulum.now()
        active_tcp_connections = 0
        need_clear_cache = False
        user_model_list = []
        trafficlog_model_list = []
        online_ip_log_model_list = []

        for user_data in data:
            user_id = user_data["user_id"]
            u = int(user_data["upload_traffic"] * ss_node.enlarge_scale)
            d = int(user_data["download_traffic"] * ss_node.enlarge_scale)
            # 个人流量增量
            user = User.get_by_pk(user_id)
            user.download_traffic += d
            user.upload_traffic += u
            user.last_use_time = log_time
            user_model_list.append(user)
            if user.overflow:
                need_clear_cache = True
            # 个人流量记录
            trafficlog_model_list.append(
                UserTrafficLog(
                    node_type=UserTrafficLog.NODE_TYPE_SS,
                    node_id=node_id,
                    user_id=user_id,
                    download_traffic=u,
                    upload_traffic=d,
                )
            )
            # 节点流量增量
            node_total_traffic += u + d
            # active_tcp_connections
            active_tcp_connections += user_data["tcp_conn_num"]
            # online ip log
            for ip in user_data.get("ip_list", []):
                online_ip_log_model_list.append(
                    UserOnLineIpLog(user_id=user_id, node_id=node_id, ip=ip)
                )

        # 用户流量
        User.objects.bulk_update(
            user_model_list, ["download_traffic", "upload_traffic", "last_use_time"],
        )
        # 节点流量记录
        SSNode.increase_used_traffic(node_id, node_total_traffic)
        # 流量记录
        UserTrafficLog.objects.bulk_create(trafficlog_model_list)
        # 在线IP
        UserOnLineIpLog.objects.bulk_create(online_ip_log_model_list)
        # 节点在线人数
        NodeOnlineLog.add_log(
            NodeOnlineLog.NODE_TYPE_SS, node_id, len(data), active_tcp_connections
        )
        # check node && user traffic
        if ss_node.overflow:
            ss_node.enable = False
        if need_clear_cache or ss_node.overflow:
            ss_node.save()
        return JsonResponse(data={})


class UserVmessConfigView(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(UserVmessConfigView, self).dispatch(*args, **kwargs)

    @method_decorator(api_authorized)
    def get(self, request, node_id):
        configs = VmessNode.get_user_vmess_configs_by_node_id(node_id)
        return JsonResponse(configs)

    @method_decorator(handle_json_post)
    @method_decorator(api_authorized)
    def post(self, request, node_id):
        node = VmessNode.get_or_none_by_node_id(node_id)
        if not node:
            return HttpResponseNotFound()

        log_time = pendulum.now()
        node_total_traffic = 0
        need_clear_cache = False
        trafficlog_model_list = []
        user_model_list = []

        for log in request.json["user_traffics"]:
            user_id = log["user_id"]
            u = int(log["ut"] * node.enlarge_scale)
            d = int(log["dt"] * node.enlarge_scale)
            # 个人流量增量
            user = User.get_by_pk(user_id)
            user.download_traffic += d
            user.upload_traffic += u
            user.last_use_time = log_time
            user_model_list.append(user)
            if user.overflow:
                need_clear_cache = True
            # 个人流量记录
            trafficlog_model_list.append(
                UserTrafficLog(
                    node_type=UserTrafficLog.NODE_TYPE_VMESS,
                    node_id=node_id,
                    user_id=user_id,
                    download_traffic=u,
                    upload_traffic=d,
                )
            )
            # 节点流量增量
            node_total_traffic += u + d
        # 节点流量记录
        VmessNode.increase_used_traffic(node_id, node_total_traffic)
        # 流量记录
        UserTrafficLog.objects.bulk_create(trafficlog_model_list)
        # TODO 在线IP
        # 个人流量记录
        User.objects.bulk_update(
            user_model_list, ["download_traffic", "upload_traffic", "last_use_time"],
        )
        # 节点在线人数
        NodeOnlineLog.add_log(
            NodeOnlineLog.NODE_TYPE_VMESS, node_id, len(request.json["user_traffics"])
        )
        # check node && user traffic
        if need_clear_cache or node.overflow:
            node.save()
        return JsonResponse(data={})


class VmessServerConfigView(View):
    @method_decorator(api_authorized)
    def get(self, request, node_id):
        node = VmessNode.get_or_none_by_node_id(node_id)
        if not node:
            return HttpResponseNotFound()
        return JsonResponse(node.server_config)


class RelayServerConfigView(View):
    @method_decorator(api_authorized)
    def get(self, request, node_id):
        node = VmessNode.get_or_none_by_node_id(node_id)
        if not node:
            return HttpResponseNotFound()
        return JsonResponse(node.relay_config)


class UserCheckInView(View):
    @method_decorator(login_required)
    def post(self, request):
        user = request.user
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
            {"title": "金额不足！", "status": "error", "subtitle": "请去捐赠界面/联系站长充值"}
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


@login_required
def change_sub_type(request):
    sub_type = request.POST.get("sub_type")
    user = request.user
    user.sub_type = sub_type
    user.save()
    res = {"title": "修改成功！", "subtitle": "订阅类型更换成功!", "status": "success"}
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
