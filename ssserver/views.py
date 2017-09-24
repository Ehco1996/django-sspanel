from django.shortcuts import render, redirect, HttpResponse, HttpResponseRedirect
from .models import SSUser
from shadowsocks.models import User
from .forms import ChangeSsPassForm, SSUserForm
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone

# Create your views here.

@permission_required('ssesrver')
def User_edit(request, pk):
    '''编辑ss_user的信息'''
    ss_user = SSUser.objects.get(pk=pk)
    contacts = User.objects.all()

    # 当为post请求时，修改数据
    if request.method == "POST":
        # 对总流量部分进行修改，转换单GB
        data = request.POST.copy()
        data['transfer_enable'] = int(eval(
            data['transfer_enable']) * settings.GB)
        form = SSUserForm(data, instance=ss_user)
        if form.is_valid():
            form.save()
            registerinfo = {
                'title': '修改成功',
                'subtitle': '数据更新成功',
                'status': 'success', }

            context = {
                'contacts': contacts,
                'registerinfo': registerinfo,
                'ss_user': ss_user,
            }
            return render(request, 'backend/userlist.html', context=context)
        else:
            registerinfo = {
                'title': '错误',
                'subtitle': '数据填写错误',
                'status': 'error', }

            context = {
                'form': form,
                'registerinfo': registerinfo,
                'contacts': contacts,
                'ss_user': ss_user,

            }
            return render(request, 'backend/useredit.html', context=context)
    # 当请求不是post时，渲染form
    else:
        # 特别初始化总流量字段
        data = {'transfer_enable': ss_user.transfer_enable / settings.GB}
        form = SSUserForm(initial=data, instance=ss_user)
        context = {
            'form': form,
            'contacts': contacts,
            'ss_user': ss_user,

        }
        return render(request, 'backend/useredit.html', context=context)


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
            return render(request, 'sspanel/userinfoedit.html', context=context)
        else:
            return redirect('/')
    else:
        form = ChangeSsPassForm()
        return render(request, 'sspanel/sspasschanged.html', {'form': form})


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
        context = {
            'registerinfo': registerinfo,
            'ss_user': ss_user,
        }
        return render(request, 'sspanel/userinfoedit.html', context=context)

    else:
        form = ChangeSsPassForm()
        return render(request, 'sspanel/sspasschanged.html', {'form': form})


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
        context = {
            'registerinfo': registerinfo,
            'ss_user': ss_user,
        }
        return render(request, 'sspanel/userinfoedit.html', context=context)

    else:
        form = ChangeSsPassForm()
        return render(request, 'sspanel/sspasschanged.html', {'form': form})


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
        context = {
            'registerinfo': registerinfo,
            'ss_user': ss_user,
        }
        return render(request, 'sspanel/userinfoedit.html', context=context)

    else:
        form = ChangeSsPassForm()
        return render(request, 'sspanel/sspasschanged.html', {'form': form})


def check_user_state():
    '''检测用户状态，将所有账号到期的用户状态重置'''
    users = User.objects.filter(level__gt=0)
    for user in users:
        # 判断用户过期时间是否大于一天
        if timezone.now() - timezone.timedelta(days=1) > user.level_expire_time:
            user.ss_user.enable = False
            user.ss_user.save()
            user.level = 0
            user.save()
            logs = 'time: {} use: {} level timeout '.format(timezone.now().strftime('%Y-%m-%d'),
                                                            user.username).encode('utf8')
            print(logs)


def auto_reset_traffic():
    '''月初重置所有免费用户流量'''
    users = User.objects.filter(level=0)

    for user in users:
        user.ss_user.download_traffic = 0
        user.ss_user.upload_traffic = 0
        user.ss_user.save()
        logs = 'user {}  traffic reset! '.format(
            user.username).encode('utf8')
        print(logs)


def auto_register(num, level=0):
    '''自动注册num个用户'''
    from random import randint
    for i in range(num):
        username = 'test' + str(i)
        code = 'testcode' + str(i)
        User.objects.create_user(
            username=username, email=None, password=None, level=level, invitecode=code)
        user = User.objects.get(username=username)
        max_port_user = SSUser.objects.order_by('-port').first()
        port = max_port_user.port + randint(2, 3)
        ss_user = SSUser.objects.create(user=user, port=port)


def clean_zombie_user(request):
    '''从未使用过的用户且从未签到过得用户'''
    import datetime
    users = User.objects.all()
    count = 0
    # 遍历所有没有签到和和没有使用过得用户
    for user in users:
        if user.ss_user.last_use_time == 0 and user.ss_user.last_check_in_time.year == 1970:
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
    return HttpResponse('ok')
