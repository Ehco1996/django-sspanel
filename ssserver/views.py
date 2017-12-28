from random import randint
import json
import base64

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import HttpResponse, HttpResponseRedirect, redirect, render
from django.utils import timezone
from shadowsocks.models import User, Node, NodeInfoLog, NodeOnlineLog
from shadowsocks.forms import UserForm
from .forms import ChangeSsPassForm, SSUserForm
from .models import SSUser, TrafficLog

# 导入加密混淆协议选项
from .models import METHOD_CHOICES, PROTOCOL_CHOICES, OBFS_CHOICES

# Create your views here.


@permission_required('ssesrver')
def User_edit(request, pk):
    '''编辑ss_user的信息'''
    ss_user = SSUser.objects.get(pk=pk)
    # 当为post请求时，修改数据
    if request.method == "POST":
        # 对总流量部分进行修改，转换单GB
        data = request.POST.copy()
        data['transfer_enable'] = int(eval(
            data['transfer_enable']) * settings.GB)
        ssform = SSUserForm(data, instance=ss_user)
        userform = UserForm(data, instance=ss_user.user)
        if ssform.is_valid() and userform.is_valid():
            ssform.save()
            userform.save()
            # 修改账户密码
            passwd = request.POST.get('resetpass')
            if len(passwd) > 0:
                ss_user.user.set_password(passwd)
                ss_user.user.save()
            registerinfo = {
                'title': '修改成功',
                'subtitle': '数据更新成功',
                'status': 'success', }
            request.session['registerinfo'] = registerinfo
            return redirect('/backend/userlist/')
        else:
            registerinfo = {
                'title': '错误',
                'subtitle': '数据填写错误',
                'status': 'error', }
            context = {
                'ssform': ssform,
                'userform': userform,
                'registerinfo': registerinfo,
                'ss_user': ss_user,
            }
            return render(request, 'backend/useredit.html', context=context)
    # 当请求不是post时，渲染form
    else:
        # 特别初始化总流量字段
        data = {'transfer_enable': ss_user.transfer_enable // settings.GB}
        passdata = {'password': ''}
        ssform = SSUserForm(initial=data, instance=ss_user)
        userform = UserForm(instance=ss_user.user)
        context = {
            'ssform': ssform,
            'userform': userform,
            'ss_user': ss_user,
        }
        return render(request, 'backend/useredit.html', context=context)


@login_required
def ChangeSsPass(request):
    '''改变用户ss连接密码'''
    ss_user = request.user.ss_user

    if request.method == 'POST':
        form = ChangeSsPassForm(request.POST)

        if form.is_valid():
            # 获取用户提交的password
            ss_pass = request.POST.get('password')
            ss_user.password = ss_pass
            ss_user.save()
            registerinfo = {
                'title': '修改成功！',
                'subtitle': '请及时更换客户端密码！',
                'status': 'success',
            }
            context = {
                'registerinfo': registerinfo,
                'ss_user': ss_user,
            }
            return redirect('/users/userinfoedit/')            
        else:
            return redirect('/')
    else:
        form = ChangeSsPassForm()
        return render(request, 'sspanel/sspasschanged.html', {'form': form})


@login_required
def ChangeSsMethod(request):
    '''改变用户ss加密'''
    ss_user = request.user.ss_user

    if request.method == 'POST':
        ss_method = request.POST.get('method')
        ss_user.method = ss_method
        ss_user.save()
        registerinfo = {
            'title': '修改成功！',
            'subtitle': '请及时更换客户端配置！',
            'status': 'success',
        }
        methods = [m[0] for m in METHOD_CHOICES]
        protocols = [p[0] for p in PROTOCOL_CHOICES]
        obfss = [o[0] for o in OBFS_CHOICES]
        context = {
            'registerinfo': registerinfo,
            'ss_user': ss_user,
            'methods': methods,
            'protocols': protocols,
            'obfss': obfss,
        }
        return render(request, 'sspanel/userinfoedit.html', context=context)


@login_required
def ChangeSsProtocol(request):
    '''改变用户ss协议'''
    ss_user = request.user.ss_user

    if request.method == 'POST':
        ss_protocol = request.POST.get('protocol')
        ss_user.protocol = ss_protocol
        ss_user.save()
        registerinfo = {
            'title': '修改成功！',
            'subtitle': '请及时更换客户端配置！',
            'status': 'success',
        }
        methods = [m[0] for m in METHOD_CHOICES]
        protocols = [p[0] for p in PROTOCOL_CHOICES]
        obfss = [o[0] for o in OBFS_CHOICES]
        context = {
            'registerinfo': registerinfo,
            'ss_user': ss_user,
            'methods': methods,
            'protocols': protocols,
            'obfss': obfss,
        }
        return render(request, 'sspanel/userinfoedit.html', context=context)


@login_required
def ChangeSsObfs(request):
    '''改变用户ss连接混淆'''
    ss_user = request.user.ss_user

    if request.method == 'POST':
        ss_obfs = request.POST.get('obfs')
        ss_user.obfs = ss_obfs
        ss_user.save()
        registerinfo = {
            'title': '修改成功！',
            'subtitle': '请及时更换客户端配置！',
            'status': 'success',
        }
        methods = [m[0] for m in METHOD_CHOICES]
        protocols = [p[0] for p in PROTOCOL_CHOICES]
        obfss = [o[0] for o in OBFS_CHOICES]
        context = {
            'registerinfo': registerinfo,
            'ss_user': ss_user,
            'methods': methods,
            'protocols': protocols,
            'obfss': obfss,
        }
        return render(request, 'sspanel/userinfoedit.html', context=context)


def check_user_state():
    '''检测用户状态，将所有账号到期的用户状态重置'''
    users = User.objects.filter(level__gt=0)
    for user in users:
        # 判断用户过期时间是否大于一天
        if timezone.now() - timezone.timedelta(days=1) > user.level_expire_time:
            user.ss_user.enable = False
            user.ss_user.upload_traffic = 0
            user.ss_user.download_traffic = 0
            user.ss_user.transfer_enable = settings.DEFAULT_TRAFFIC
            user.ss_user.save()
            user.level = 0
            user.save()
            logs = 'time: {} use: {} level timeout '.format(timezone.now().strftime('%Y-%m-%d'),
                                                            user.username).encode('utf8')
            print(logs)
    print('Time:{} CHECKED'.format(timezone.now()))


def auto_reset_traffic():
    '''月初重置所有免费用户流量'''
    users = User.objects.filter(level=0)

    for user in users:
        user.ss_user.download_traffic = 0
        user.ss_user.upload_traffic = 0
        user.ss_user.transfer_enable = settings.DEFAULT_TRAFFIC
        user.ss_user.save()
        logs = 'user {}  traffic reset! '.format(
            user.username).encode('utf8')
        print(logs)


def clean_traffic_log():
    '''月初清空所有流量记录'''
    res = TrafficLog.objects.all().delete()
    log = str(res)
    print('all traffic record removed!:{}'.format(log))


def clean_online_log():
    '''月初清空所有在线记录'''
    res = NodeOnlineLog.objects.all().delete()
    log = str(res)
    print('all online record removed!:{}'.format(log))


def clean_node_log():
    '''月初清空所有节点负载记录'''
    res = NodeInfoLog.objects.all().delete()
    log = str(res)
    print('all node info record removed!:{}'.format(log))


def auto_register(num, level=0):
    '''自动注册num个用户'''
    for i in range(num):
        username = 'test' + str(i)
        code = 'testcode' + str(i)
        User.objects.create_user(
            username=username, email=None, password=None, level=level, invitecode=code)
        user = User.objects.get(username=username)
        max_port_user = SSUser.objects.order_by('-port').first()
        port = max_port_user.port + randint(2, 3)
        ss_user = SSUser.objects.create(user=user, port=port)


@permission_required('ssesrver')
def clean_zombie_user(request):
    '''清楚从未使用过的用户'''
    import datetime
    users = User.objects.all()
    count = 0
    for user in users:
        if user.ss_user.last_use_time == 0:
            user.delete()
            count += 1
    registerinfo = {
        'title': '删除僵尸用户',
        'subtitle': '成功删除{}个僵尸用户'.format(count),
                    'status': 'success', }
    context = {
        'registerinfo': registerinfo
    }
    return render(request, 'backend/index.html', context=context)


def testcheck(request):
    '''test url '''
    # auto_register(10)
    # do some test page
    # check_user_state()
    # clean_traffic_log()
    return HttpResponse('ok')


def Subscribe(request, token):
    '''
    返回ssr订阅链接
    '''
    username = token.split('&&')[0]
    user = base64.b64decode(username).decode('utf8')
    try:
        user = User.objects.get(username=user)
        ss_user = user.ss_user
    except:
        return HttpResponse('ERROR')
    # 验证token
    keys = base64.b64encode(bytes(user.username, 'utf-8')).decode('ascii') + \
        '&&' + base64.b64encode(bytes(user.password, 'utf-8')).decode('ascii')
    if token == keys:
        # 生成订阅链接部分
        sub_code = ''
        # 遍历该用户所有的节点
        node_list = Node.objects.filter(level__lte=user.level, show='显示')
        for node in node_list:
            sub_code = sub_code + node.get_ssr_link(ss_user) + "\n"
        sub_code = base64.b64encode(bytes(sub_code, 'utf8')).decode('ascii')
        return HttpResponse(sub_code)
    else:
        return HttpResponse('ERROR')
