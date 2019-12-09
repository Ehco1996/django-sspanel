# Ubuntu18.04部署django-sspanel

## 更新系统
```
apt-get update
apt-get upgrade
```
## 安装mysql和ngnix
```
apt-get install mysql-client mysql-server
apt-get install nginx
```

## 安装pyenv
* 安装依赖包
```
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
xz-utils tk-dev libffi-dev liblzma-dev libedit-dev
```
* 一键安装
```
curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash
```
* 修改配置文件：`~/.bashrc`。将以下内容添加到最后。
```
export PATH="/root/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```
* 使配置生效。
```
# 使自己的profile生效
source ~/.bashrc
```
* 使用`pyenv`安装`python3`
```
pyenv install 3.7.5
```
* 创建Django-sspanel 运行的虚拟环境
```
pyenv virtualenv 3.7.5 venv-sspanel
```

## Clone项目并安装第三方库

* 创建并切换目录：`/home/www/`
```
mkdir /home/www
cd /home/www/
```
* clone 项目到本地。注意：dev为最新分支。
```
 git clone -b dev https://github.com/algoboy101/django-sspanel.git
 cd /home/www/django-sspanel
 git branch
```
* 将项目文件夹的环境设置为 virtualenv
```
pyenv local venv-sspanel
```
* 安装第三方包
```
apt-get install libmysqlclient-dev
pip install mysqlclient
```
* 修改`requirements.txt`文件：`Django>=2.2.1` -> `Django==2.2.1`。并安装依赖。
```
pip install -r requirements.txt 
```


## 设置mysql并创建数据库

### 设置编码
* 参考 [(1366, "Incorrect string value: '\xE7\x94\xA8\xE6\x88\xB7' for column 'name'_实战问答](https://coding.imooc.com/learn/questiondetail/25427.html) 修改编码配置文件。`vim /etc/mysql/mysql.conf.d/mysqld.cnf`。
* 在文件最后添加以下内容。

```
character-set-server=utf8
collation-server=utf8_general_ci
init_connect='SET NAMES utf8'

[client]
default-character-set=utf8
```
* 重启mysql，生效。
```
service mysql restart
```

### 其它设置
* 参考 [MySQL----mysql_secure_installation 安全配置向导 - 勿忘初心的博客](https://blog.csdn.net/qq_32786873/article/details/78846008) 完成安全设置。
* 参考 [ERROR 1819 (HY000): Your password does not satisfy the current policy requirements - Spring Boot-Common On With You](https://blog.csdn.net/hello_world_qwp/article/details/79551789) 设置密码策略。
```
# 密码安全级别：低
set global validate_password_policy=LOW;
# 最小长度：6
set global validate_password_length=6; 
```
* 参考 [MySQL安装后无法用root用户访问的问题 - 行走—舒 - 博客园](https://www.cnblogs.com/shuyuq/p/10370700.html)，解决root访问不需要密码的问题。
* 思路是：新建一个用户：`django`，拥有所有权限。（密码是：django，注意修改）。
```
# 创建用户
grant all privileges on *.* to 'django'@'localhost' identified by 'django';
# 查看所有用户列表，看到django。
SELECT User, Host, HEX(authentication_string) FROM mysql.user;
```
* 验证是否能够通过密码登录。执行命令：`mysql -u django -p django`。

### 创建数据库
* 参考 [MySQL删除数据库（DROP DATABASE语句）](http://c.biancheng.net/view/2415.html)，创建数据库：`sspanel`，用于django-sspanel。
```
# 创建命令
CREATE DATABASE sspanel;
# 删除命令
# DROP DATABASE sspanel;
# 查看数据库列表，看到sspanel数据库
show databases;
```



## 配置django-sspanel
* 配置文件目录：`/home/www/django-sspanel/configs/`
```
# 进入配置文件夹
cd configs

# 配置文件结构
➜ tree
.
├── __init__.py
├── default
│   ├── __init__.py
│   ├── cron.py # 设置计划任务
│   ├── db.py   # 设置数据库
│   ├── email.py # 设置邮箱
│   └── sites.py # 设置杂七杂八的东西
├── development.py
├── mysqld
│   └── mysqld_charset.cnf
├── nginx
│   └── nginx.example.conf
└── production.py # 设置数据库密码

**每一项配置文件都要打开进去自己设置~**
```
### 修改配置文件中数据库相关的用户名和密码
* 修改 `/home/www/django-sspanel/configs/default/db.py`
```
# mysql 设置
DATABASES = {
    "default": {
        "ENGINE": "django_prometheus.db.backends.mysql",
        "NAME": "sspanel",
        "USER": "django", # 用户名 （和前面对应）
        "PASSWORD": "django", # 密码 （和前面对应）
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "OPTIONS": {
            "autocommit": True,
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            "charset": "utf8mb4",
        },
    }
}
```

* 修改 `/home/www/django-sspanel/configs/production.py`
```
DATABASES["default"].update(
    {
        "PASSWORD": os.getenv("MYSQL_PASSWORD", "django"), # 密码
        "HOST": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "USER": os.getenv("MYSQL_USER", "django"), # 用户名
    }
)
```


## 配置ngnix
* `vim /etc/nginx/conf.d/vhost.conf`，填入以下内容。
```
server {
        listen 80;
        server_name css.xuezhisd.top; # 项目域名
        root  /home/www/django-sspanel; # 项目的目录

        location /media  {
            alias /home/www/django-sspanel/media;  # your Django project's media files - amend as required
        }

        location /static
        {
          alias  /home/www/django-sspanel/static; #静态文件地址，js/css
          expires  12h;
        }

        location /
        {
          include uwsgi_params;
          uwsgi_pass 127.0.0.1:8080;
        }
}
```
* 重启。
```
service nginx restart
```


## 测试
### 测试项目是否正常运行。
```
    $  cd .. # 切回项目根目录
    $  python manage.py migrate # 通过djang ORM 建立所需数据库表   
    $  python manage.py runserver # 测试项目是否运行
    $  python manage.py collectstatic # 收集静态文件
创建管理员账号
    $  python manage.py createsuperuser # 按照提示创建即可
```
### 启动并访问
* 执行以下命令，启动。
```
uwsgi uwsgi.ini
```
* 访问`http://ip/`,即可看到网页。

## 设置crontab任务
```
python manage.py crontab add
``







## 参考：
* [pyenv快速入门 - 简书](https://www.jianshu.com/p/f15cb9571cab)
* [MySQL删除数据库（DROP DATABASE语句）](http://c.biancheng.net/view/2415.html)
* [(1366, "Incorrect string value: '\xE7\x94\xA8\xE6\x88\xB7' for column 'name'_实战问答](https://coding.imooc.com/learn/questiondetail/25427.html)
