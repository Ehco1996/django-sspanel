#!/bin/bash
parm="$1"
main(){
    if [ -z "$parm" ]; then
            exit 1
    fi

    if 	[[ "$parm" = "restart" ]];then
        Restart
    elif [ "$parm" = "stop" ] ; then
        Stop
    else
    echo "???" >> /root/v2scar/restartLog.txt
    fi
}

Restart(){
    currTime=$(date +"%Y-%m-%d %T")
    echo "$currTime 重启成功" >> /root/v2scar/restartLog.txt
    docker restart v2scar
    docker restart v2ray
}
Stop(){
    docker stop v2scar
    docker stop v2ray
}

main
