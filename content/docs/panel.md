---
title: "前端面板部署教程"
date: 2021-01-24T15:39:50+08:00
weight: 1
draft: false
tags: ["前端", "docker"]
description: "面板部署教程"
author: "Ehco1996"
showToc: true
TocOpen: false
---

> 本篇教程采用docker来对接, 用docker可以给你省去很多麻烦

<!--more-->

### 视频教程

面板视频安装教程: [地址](https://youtu.be/BRHcdGeufvY)

### 安装docker

根据自己的系统

安装 `docker` 和 `docker-compose`

教程: <https://docs.docker.com/install/>

### 下载源码

 `git clone https://github.com/Ehco1996/django-sspanel.git`

### 配置信息

 `cd django-sspanel`

**所有的配置都在 `django-sspanel/configs` 里**

> 每个配置文件都可以根据自己的需求来更改

``` bash
├── default
│   ├── __init__.py
│   ├── common.py  # django配置 忽略
│   ├── cron.py    # 计划任务
│   ├── db.py      # 数据库
│   ├── email.py   # 邮箱
│   └── sites.py   # 站点信息配置
├── mysqld
│   └── mysqld_charset.cnf  # mysql docker配置 可以不用管
├── nginx
│   └── nginx.example.conf # nginx docker 配置 需要手动配置
├── development.py # 开发调试用
└── production.py  # 生产环境配置

```

详细说一下： `nginx.example.conf`

``` nginx
server {
    listen 80;
    server_name _; # 这个地方填写你的域名或者你的ip
    root /src/django-sspanel;

    location /static {
        alias /src/django-sspanel/static; #静态文件地址，js/css
        expires 12h;
    }

    location / {
        include uwsgi_params;
        uwsgi_pass web:8080;
    }

    location = /favicon.ico {
        empty_gif;
    }
}

```

### 运行项目

``` bash
# 进入项目根目录
cd django-sspanel

# 复制环境变量文件
cp .env.sample .env

# 将你的自定义配置写在里面
vim .env

# 收集静态资源
docker-compose run --rm web python manage.py collectstatic --noinput

# 创建数据库表
docker-compose run --rm web python manage.py migrate

# 创建超级用户账号
docker-compose run --rm web python manage.py create_admin --email "admin@ss.com" --username "admin1" --password "adminadmin"

# 关闭刚才创建的脚本服务
docker-compose down

# 开启程序并放在后台运行
docker-compose up -d

```

访问你的域名吧~
