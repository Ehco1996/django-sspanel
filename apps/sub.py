import base64
from collections import defaultdict
from uuid import uuid4

from django.conf import settings
from django.template.loader import render_to_string

from apps import utils
from apps.proxy import models as pm
from apps.sspanel import models as sm


class UserSubManager:
    """统一管理用户的订阅"""

    SUB_TYPE_SS = "ss"
    SUB_TYPE_VLESS = "vless"
    SUB_TYPE_TROJAN = "trojan"
    SUB_TYPE_CLASH = "clash"
    SUB_TYPE_CLASH_PRO = "clash_pro"

    SUB_TYPES_SET = {
        SUB_TYPE_SS,
        SUB_TYPE_VLESS,
        SUB_TYPE_TROJAN,
        SUB_TYPE_CLASH,
        SUB_TYPE_CLASH_PRO,
    }

    def __init__(self, user, sub_type, request):
        self.user = user
        if sub_type not in self.SUB_TYPES_SET:
            sub_type = self.SUB_TYPE_SS
        self.sub_type = sub_type
        self.node_list = self._fill_fake_node()
        sm.UserSubLog.add_log(user, sub_type, utils.get_client_ip(request))

    def _fill_fake_node(self):
        """根据用户信息拿出所有需要的node并添加一些虚拟节点
        - 官网地址
        - 增加用户 等级，
        - 流量使用情况
        """
        node_list = pm.ProxyNode.get_active_nodes(level=self.user.level)
        fake_node = []
        note_list = [
            f"{settings.TITLE}官网：{settings.HOST}",
        ]
        if len(node_list) > 0:
            note_list.extend(
                [
                    f"等级：{self.user.level} 到期时间：{self.user.level_expire_time.date()}",
                    f"剩余流量：{self.user.human_remain_traffic},总流量：{self.user.human_total_traffic}",
                ]
            )
        else:
            note_list.append("没有可以用的节点哦 请去官网购买")

        for note in note_list:
            node = pm.ProxyNode(name=note, server=uuid4().hex)
            pm.SSConfig(proxy_node=node)
            fake_node.append(node)

        return fake_node + node_list

    def get_clash_sub_links(self):
        node_configs = []
        relay_node_group = defaultdict(list)
        for node in self.node_list:
            if node.enable_relay:
                for rule in node.relay_rules.filter(relay_node__enable=True):
                    relay_node_group[rule.relay_node].append(
                        {
                            "clash_config": node.get_user_clash_config(self.user, rule),
                            "name": rule.remark,
                        }
                    )
            else:
                node_configs.append(
                    {
                        "clash_config": node.get_user_clash_config(self.user),
                        "name": node.name,
                    }
                )
        for cfg_list in relay_node_group.values():
            node_configs.extend(cfg_list)
        return render_to_string(
            "yamls/clash.yml", {"nodes": node_configs, "sub_type": self.sub_type}
        )

    def get_normal_sub_links(self):
        sub_links = ""
        relay_node_group = defaultdict(list)
        for node in self.node_list:
            if node.enable_relay:
                for rule in node.relay_rules.filter(relay_node__enable=True):
                    relay_node_group[rule.relay_node].append(
                        node.get_user_node_link(self.user, rule)
                    )
            else:
                sub_links += node.get_user_node_link(self.user) + "\n"
        for sub_link_list in relay_node_group.values():
            for link in sub_link_list:
                sub_links += link + "\n"
        sub_links = base64.urlsafe_b64encode(sub_links.encode()).decode()
        return sub_links

    def get_sub_links(self):
        if self.sub_type in [self.SUB_TYPE_CLASH, self.SUB_TYPE_CLASH_PRO]:
            return self.get_clash_sub_links()
        return self.get_normal_sub_links()
