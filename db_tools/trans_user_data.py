'''
数据库转换工具

魔改 -> django-sspanel

用法：
以json格式导出魔改的user表，命名为user.json,并将json文件放入data目录

仅迁移用户的：

username,email,level,level_expire_time,blance,u,t,d,passwd,transfer_enable,method,protocol,obfs

用户的密码为用户名+abc
用户的端口会重置
'''
import sys
import os
import json
from random import randint
from datetime import datetime
import django

# 启动django配置
pwd = os.path.dirname(os.path.realpath(__file__))
sys.path.append(pwd + "/../")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django-sspanel.settings")
django.setup()
from shadowsocks.models import User
from ssserver.models import SSUser


def trans_data(user_data):
    # 开始数据转换
    for data in user_data:
        try:
            raw_ime = data['class_expire'].split(' ')[0].split('/')
            time_formated = datetime(year=int(raw_ime[2]), month=int(
                raw_ime[1]), day=int(raw_ime[0]))
            user = User.objects.create_user(
                username=data['user_name'],
                email=data['email'],
                password=data['user_name'] + 'abc',
                invitecode='None',
                invitecode_num=data['invite_num'],
                level=data['class'],
                level_expire_time=time_formated,
                balance=data['money'],
            )
            if len(SSUser.objects.all()) == 0:
                port = 1025
            else:
                max_port_user = SSUser.objects.order_by(
                    '-port').first()
                port = max_port_user.port + randint(1, 3)
                ss_user = SSUser.objects.create(
                    user=user,
                    port=port,
                    upload_traffic=data['u'],
                    download_traffic=data['d'],
                    last_use_time=data['t'],
                    transfer_enable=data['transfer_enable'],
                    method=data['method'],
                    protocol=data['protocol'],
                    obfs=data['obfs'],
                    level=data['class'],
                )
        except:
            print('用户：{} 资料转移失败，请保证数据来源准确！'.format(data['user_name']))


def main():
    try:
        # 读入user数据
        with open(pwd + '/data/user.json', 'r') as f:
            user_data = json.loads(f.read())['RECORDS']
    except:
        print('请保证将魔改user表导出为user.json，并放在data目录下')

    trans_data(user_data)


if __name__ == '__main__':
    main()
