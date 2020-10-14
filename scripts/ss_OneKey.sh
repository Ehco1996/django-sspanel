#!/bin/bash
clear
echo
echo "#################################################################"
echo "django-sspanel ss 一键后端"
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
    API="\"http:\/\/$Domain\/api\/user_ss_config\/$NodeId\/?token=$Token\""
    echo "API = http://$Domain/api/user_ss_config/$NodeId/?token=$Token"
    echo "按任意键开始安装"
    read A
}
prepare_Centos(){
    yum install -y curl git jq
}
prepare_Debian(){
    apt install -y curl git jq
}
End(){
    echo "安装完毕 请打开防火墙 1000-2000 端口"
    echo "请按任意键退出脚本"
    read A
}
Install(){
    curl -sSL https://get.docker.com/ | sh
    curl -L "https://github.com/docker/compose/releases/download/1.23.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
    curl -sL https://api.github.com/repos/Ehco1996/aioshadowsocks/releases/latest \
    | jq -r '.zipball_url' \
    | wget -qi - -O aioshadowsocks.zip
    unzip aioshadowsocks.zip
    rm aioshadowsocks.zip
    sspath="$(find . -type d -name "*aioshadowsocks*")"
    echo $sspath
    cd $sspath
    systemctl restart docker
    sed -i 's/SS_API_ENDPOINT: \"\"/SS_API_ENDPOINT: '"$API"'/g' docker-compose.yml
    docker-compose up -d
    chkconfig docker on
    End
}

centos_install(){
    APIinit
    prepare_Centos
    Install
    systemctl enable docker.service
}

debian_install(){
    APIinit
    prepare_Debian
    Install
}
system_check


