from django.shortcuts import render, redirect
from .models import SSUser
from shadowsocks.models import User
from .forms import ChangeSsPassForm, SSUserForm
from django.conf import settings
# Create your views here.


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
            return render(request, 'sspanel/userinfo.html', context=context)
        else:
            return redirect('/')
    else:
        form = ChangeSsPassForm()
        return render(request, 'sspanel/sspasschanged.html', {'form': form})


def User_edit(request, pk):
    '''编辑ss_user的信息'''
    ss_user = SSUser.objects.get(pk=pk)
    contacts = User.objects.all()

    # 当为post请求时，修改数据
    if request.method == "POST":
        # 对总流量部分进行修改，转换单GB
        data = request.POST.copy()
        data['transfer_enable'] = str(
            int(data['transfer_enable']) * settings.GB)
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
        form = SSUserForm(instance=ss_user)
        context = {
            'form': form,
            'contacts': contacts,
            'ss_user': ss_user,

        }
        return render(request, 'backend/useredit.html', context=context)


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
        return render(request, 'sspanel/userinfo.html', context=context)
        
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
        return render(request, 'sspanel/userinfo.html', context=context)
        
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
        return render(request, 'sspanel/userinfo.html', context=context)
        
    else:
        form = ChangeSsPassForm()
        return render(request, 'sspanel/sspasschanged.html', {'form': form})
