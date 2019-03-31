import time

import pendulum
from django.views import View
from django.db.models import F
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import HttpResponse
from ratelimit.decorators import ratelimit
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, permission_required

from apps.payments import pay
from apps.constants import NODE_USER_INFO_TTL
from apps.utils import traffic_format, simple_cached_view, get_node_user, authorized
from apps.ssserver.models import Suser, TrafficLog, Node, NodeOnlineLog, AliveIp
from apps.sspanel.models import InviteCode, Goods, User, Donate, UserOrder


@permission_required("sspanel")
def userData(request):
    """
    返回用户信息：
    在线人数、今日签到、从未签到、从未使用
    """

    data = [
        NodeOnlineLog.totalOnlineUser(),
        User.get_today_register_user().count(),
        Suser.get_today_checked_user_num(),
        Suser.get_never_checked_user_num(),
        Suser.get_never_used_num(),
    ]
    return JsonResponse({"data": data})


@permission_required("sspanel")
def nodeData(request):
    """
    返回节点信息
    所有节点名
    各自消耗的流量
    """
    nodeName = [node.name for node in Node.objects.filter(show=1)]

    nodeTraffic = [
        round(node.used_traffic / settings.GB, 2)
        for node in Node.objects.filter(show=1)
    ]

    data = {"nodeName": nodeName, "nodeTraffic": nodeTraffic}
    return JsonResponse(data)


@permission_required("sspanel")
def donateData(request):
    """
    返回捐赠信息
    捐赠笔数
    捐赠总金额
    """
    data = [Donate.totalDonateNums(), int(Donate.totalDonateMoney())]
    return JsonResponse({"data": data})


@login_required
def change_ss_port(request):
    """
    随机重置用户用端口
    返回是否成功
    """
    user = request.user.ss_user
    # 找到端口池中最大的端口
    port = Suser.get_random_port()
    user.port = port
    user.save()
    registerinfo = {
        "title": "修改成功！",
        "subtitle": "端口修改为：{}！".format(port),
        "status": "success",
    }
    return JsonResponse(registerinfo)


@login_required
def gen_invite_code(request):
    """
    生成用户的邀请码
    返回是否成功
    """
    u = request.user
    if u.is_superuser is True:
        # 针对管理员特出处理，每次生成5个邀请码
        num = 5
    else:
        num = u.invitecode_num - len(InviteCode.objects.filter(code_id=u.pk))
    if num > 0:
        for i in range(num):
            code = InviteCode(code_type=0, code_id=u.pk)
            code.save()
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
def traffic_query(request):
    """
    流量查请求
    """
    node_id = request.POST.get("node_id", 0)
    node_name = request.POST.get("node_name", "")
    user_id = request.user.pk
    now = pendulum.now()
    last_week = [now.subtract(days=i).date() for i in range(6, -1, -1)]
    labels = ["{}-{}".format(t.month, t.day) for t in last_week]
    traffic_data = [
        TrafficLog.get_traffic_by_date(node_id, user_id, t) for t in last_week
    ]
    total = TrafficLog.get_user_traffic(node_id, user_id)
    title = "节点 {} 当月共消耗：{}".format(node_name, total)

    configs = {
        "title": title,
        "labels": labels,
        "data": traffic_data,
        "data_title": node_name,
        "x_label": "日期 最近七天",
        "y_label": "流量 单位：MB",
    }
    return JsonResponse(configs)


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


@authorized
@csrf_exempt
@require_http_methods(["POST"])
def get_invitecode(request):
    """
    获取邀请码接口
    只开放给管理员账号
    返回一个没用过的邀请码
    需要验证token
    """
    admin_user = User.objects.filter(is_superuser=True).first()
    code = InviteCode.objects.filter(code_id=admin_user.pk, isused=False).first()
    if code:
        return JsonResponse({"msg": code.code})
    else:
        return JsonResponse({"msg": "邀请码用光啦"})


@authorized
@simple_cached_view()
@require_http_methods(["GET"])
def node_api(request, node_id):
    """
    返回节点信息
    筛选节点是否用光
    """
    node = Node.objects.filter(node_id=node_id).first()
    if node and node.used_traffic < node.total_traffic:
        data = (node.traffic_rate,)
    else:
        data = None
    res = {"ret": 1, "data": data}
    return JsonResponse(res)


@authorized
@csrf_exempt
@require_http_methods(["POST"])
def node_online_api(request):
    """
    接受节点在线人数上报
    """
    data = request.json
    node = Node.objects.filter(node_id=data["node_id"]).first()
    if node:
        NodeOnlineLog.objects.create(
            node_id=data["node_id"],
            online_user=data["online_user"],
            log_time=int(time.time()),
        )
    res = {"ret": 1, "data": []}
    return JsonResponse(res)


@authorized
@simple_cached_view(ttl=NODE_USER_INFO_TTL)
@require_http_methods(["GET"])
def user_api(request, node_id):
    """
    返回符合节点要求的用户信息
    """
    data = get_node_user(node_id)
    res = {"ret": 1, "data": data}
    return JsonResponse(res)


@authorized
@csrf_exempt
@require_http_methods(["POST"])
def traffic_api(request):
    """
    接受服务端的用户流量上报
    """
    data = request.json
    node_id = data["node_id"]
    traffic_list = data["data"]
    log_time = int(time.time())

    node_total_traffic = 0
    trafficlog_model_list = []

    for rec in traffic_list:
        user_id = rec["user_id"]
        u = rec["u"]
        d = rec["d"]
        # 个人流量增量
        Suser.objects.filter(user_id=user_id).update(
            download_traffic=F("download_traffic") + d,
            upload_traffic=F("upload_traffic") + u,
            last_use_time=log_time,
        )
        # 个人流量记录
        trafficlog_model_list.append(
            TrafficLog(
                node_id=node_id,
                user_id=user_id,
                traffic=traffic_format(u + d),
                download_traffic=u,
                upload_traffic=d,
                log_time=log_time,
            )
        )
        # 节点流量增量
        node_total_traffic += u + d
    # 节点流量记录
    Node.objects.filter(node_id=node_id).update(
        used_traffic=F("used_traffic") + node_total_traffic
    )
    # 流量记录
    TrafficLog.objects.bulk_create(trafficlog_model_list)
    return JsonResponse({"ret": 1, "data": []})


@authorized
@csrf_exempt
@require_http_methods(["POST"])
def alive_ip_api(request):
    data = request.json
    node_id = data["node_id"]
    model_list = []
    for user_id, ip_list in data["data"].items():
        user = User.objects.get(id=user_id)
        for ip in ip_list:
            model_list.append(AliveIp(node_id=node_id, user=user.username, ip=ip))
    AliveIp.objects.bulk_create(model_list)
    res = {"ret": 1, "data": []}
    return JsonResponse(res)


@login_required
def checkin(request):
    """用户签到"""
    ss_user = request.user.ss_user
    res, traffic = ss_user.checkin()
    if res:
        data = {
            "title": "签到成功！",
            "subtitle": "获得{}流量！".format(traffic_format(traffic)),
            "status": "success",
        }
    else:
        data = {"title": "签到失败！", "subtitle": "距离上次签到不足一天", "status": "error"}
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["POST"])
def ailpay_callback(request):
    data = dict(request.POST)
    signature = data.pop("sign")
    success = pay.alipay.verify(data, signature)
    if success and data["trade_status"] in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        order = UserOrder.objects.get(out_trade_no=data["out_trade_no"])
        order.handle_paid()
        return HttpResponse("success")
    else:
        return HttpResponse("failure")


class OrderView(View):
    def get(self, request):
        user = request.user
        order = UserOrder.get_recent_created_order(user)
        order and order.check_order_status()
        if order and order.status == UserOrder.STATUS_FINISHED:
            info = {"title": "充值成功!", "subtitle": "请去商品界面购买商品！", "status": "success"}
        else:
            info = {"title": "支付查询失败!", "subtitle": "亲，确认支付了么？", "status": "error"}
        return JsonResponse({"info": info})

    @ratelimit(key="user", rate="1/1s")
    def post(self, request):
        amount = int(request.POST.get("num"))

        if amount < 1:
            info = {"title": "失败", "subtitle": "请保证金额大于1元", "status": "error"}
        else:
            order = UserOrder.get_or_create_order(request.user, amount)
            info = {
                "title": "请求成功！",
                "subtitle": "支付宝扫描下方二维码付款，付款完成记得按确认哟！",
                "status": "success",
            }
        return JsonResponse(
            {"info": info, "qrcode_url": order.qrcode_url, "order_id": order.id}
        )
