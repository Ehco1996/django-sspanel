---
title: "shadowsocks/v2ray服务端部署教程"
date: 2021-01-24T15:57:00+08:00
weight: 2
draft: false
tags: ["后端", "shadowsocks", "v2ray"]
description: "服务端部署教程"
author: "Ehco1996"
showToc: true
TocOpen: false
---

> 目前支持 shadowsocks 和 v2ray 这两种服务端

<!--more-->

## 视频教程

后端对接视频教程: [地址](https://youtu.be/QNbnya1HHU0)

## Shadowsocks 安装教程

后端地址：<https://github.com/Ehco1996/aioshadowsocks>

* 在面板后台添加一个类型为 `ss` 的节点

* 填写好对应配置后点开对接按钮（小火箭图标）

![2](https://user-images.githubusercontent.com/24697284/74079160-8b2c0f80-4a6e-11ea-849b-eeba2acd0da7.png)

* 复制好 对应的 **对接地址（注意这个地址不能暴露给其他人）**

![3](https://user-images.githubusercontent.com/24697284/74079185-e6f69880-4a6e-11ea-8a40-fe8f856754eb.png)

* 下载代码

 `git clone https://github.com/Ehco1996/aioshadowsocks.git`

* 编辑 `docker-compose.yml` 并将对接地址复制到文件的 `SS_API_ENDPOINT`字段

``` yml
  version: '3'
  services:
    ss:
      container_name : aioshadowsocks
      image: ehco1996/aioshadowsocks:runtime
      network_mode: host
      restart: always
      environment:
        SS_API_ENDPOINT: "http://127.0.0.1:8000/api/user_ss_config/1/?token=youowntoken"
        SS_LOG_LEVEL: "info"
        SS_SYNC_TIME: 60
        SS_GRPC_HOST: "127.0.0.1"
        SS_GRPC_PORT: 5000
      logging:
        driver: "json-file"
        options:
            max-size: "100k"
      volumes:

        - .:/src/aioshadowsocks

      working_dir: /src/aioshadowsocks
      command: ["python", "-m", "shadowsocks", "run_ss_server"]
  ```

* 启动服务端 `docker-compose up`

## V2ray 安装教程

后端地址：<https://github.com/Ehco1996/v2scar>

* 在面板添加`v2ray`节点

* 点开对接按钮 对接按钮

![v1](https://user-images.githubusercontent.com/24697284/74079343-0db5ce80-4a71-11ea-9f61-58811771748b.png)

* 克隆或下载 v2scar

 `git clone https://github.com/Ehco1996/v2scar.git`

* 编辑 `docker-compose.yml` 并将**对接地址**复制到文件的 `V2SCAR_API_ENDPOINT`字段 , **Vmess 配置地址** 复制到v2ray的启动命令处

``` yml
version: '3'

services:
  v2ray:
    image: v2fly/v2fly-core:latest
    container_name: v2ray
    restart: always
    volumes:

      - ./v2ray-config.json:/etc/v2ray/config.json

    ports:

      - "10086:10086"

    # 复制启动地址
    command: ["v2ray","-config=http://127.0.0.1:8000/api/vmess_server_config/2/?token=youowntoken"]

  v2scar:
    container_name : v2scar
    image: ehco1996/v2scar
    restart: always
    depends_on:

      - v2ray

    links:

      - v2ray

    environment:
      V2SCAR_SYNC_TIME: 60
      # 复制对接地址
      V2SCAR_API_ENDPOINT: "http://127.0.0.1:8000/api/user_vmess_config/2/?token=youowntoken"
      V2SCAR_GRPC_ENDPOINT: "v2ray:8080"
```

* 启动v2ray程序 `docker-compose up`
