from django.shortcuts import render,redirect
from .models import SSUser

from .forms import ChangeSsPassForm
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
                'ss_user':ss_user,
            }
            return render(request, 'sspanel/userinfo.html', context=context)
        else:
            return redirect('/')
    else:
        form = ChangeSsPassForm()
        return render(request, 'sspanel/sspasschanged.html', {'form': form})
