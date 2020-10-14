#!/bin/bash
clear
echo
echo "#################################################################"
echo "django-sspanel V2ray 一键后端"
echo
echo "System Required: CentOS Debian"
echo "#################################################################"
echo


system_check(){
	if [ -f /usr/bin/yum ]; then
		centos_install
	elif [ -f /usr/bin/apt ]; then
		debian_install
	else
		echo -e "你的系统不支持"
	fi
}

APIinit(){
echo "请输入面板地址(Example:sspanel.com)"
read Domain
echo "请输入Token"
read Token
echo "请输入节点ID"
read NodeId
API="\"http:\/\/$Domain\/api\/user_vmess_config\/$NodeId\/?token=$Token\""
echo "API = http://$Domain/api/user_vmess_config/$NodeId/?token=$Token"
echo "按任意键开始安装"
read A
}

prepare_Centos(){
    yum install -y curl git
}
prepare_Debian(){
    apt install -y curl git
}
End(){
    echo "安装完毕 请打开防火墙端口 (默认10086)"
    echo "请按任意键退出脚本"
    read A
}
install(){
    curl -sSL https://get.docker.com/ | sh
    curl -L "https://github.com/docker/compose/releases/download/1.23.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
    systemctl enable docker
    systemctl enable docker.service
    systemctl restart docker
    git clone https://github.com/Ehco1996/v2scar.git
    cd v2scar
    sed -i 's/V2SCAR_API_ENDPOINT: \"\"/V2SCAR_API_ENDPOINT: '"$API"'/g' docker-compose.yml
    docker-compose up -d
AutoRestart
    End
}

centos_install(){
    APIinit
    prepare_Centos
    install
}

debian_install(){
    APIinit
    prepare_Debian
    install
}

AutoRestart(){
    echo "添加重启服务"
    cd
    cd /root/v2scar
    wget -N --no-check-certificate https://raw.githubusercontent.com/jackjieYYY/django-sspanel_script/master/v2ray/v2ray.sh && chmod +x v2ray.sh
    cd
    cd /etc/systemd/system
    wget -N --no-check-certificate https://raw.githubusercontent.com/jackjieYYY/django-sspanel_script/master/v2ray/sspanel_V2ray.service && chmod +x sspanel_V2ray.service
    wget -N --no-check-certificate https://raw.githubusercontent.com/jackjieYYY/django-sspanel_script/master/v2ray/sspanel_Vray.timer && chmod +x sspanel_Vray.timer
    systemctl enable sspanel_V2ray.service
    systemctl enable sspanel_Vray.timer
    systemctl daemon-reload
    systemctl start sspanel_V2ray.service
    systemctl start sspanel_Vray.timer
    cd
}

system_check


