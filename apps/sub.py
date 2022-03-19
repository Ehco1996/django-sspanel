import base64
from collections import defaultdict

from django.conf import settings
from django.template.loader import render_to_string

from apps.proxy import models as pm


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

    def __init__(self, user, sub_type, node_list):
        self.user = user
        if sub_type not in self.SUB_TYPES_SET:
            sub_type = self.SUB_TYPE_SS
        self.sub_type = sub_type
        self.node_list = node_list

    def get_sub_info(self):
        if self.sub_type in [self.SUB_TYPE_CLASH, self.SUB_TYPE_CLASH_PRO]:
            return self.get_clash_sub_yaml()
        return self.get_ss_sub_links()

    def get_ss_sub_links(self):
        sub_links = ""
        relay_node_group = defaultdict(list)
        for node in self.node_list:
            if node.enable_relay:
                for rule in node.relay_rules.filter(relay_node__enable=True):
                    relay_node_group[rule.relay_node].append(
                        node.get_user_node_link(self.user, rule)
                    )
            if node.enable_direct:
                sub_links += node.get_user_node_link(self.user) + "\n"
        for sub_link_list in relay_node_group.values():
            for link in sub_link_list:
                sub_links += link + "\n"
        sub_links = base64.urlsafe_b64encode(sub_links.encode()).decode()
        return sub_links

    def get_clash_sub_yaml(self):
        return render_to_string(
            "clash/main.yaml",
            {
                "sub_type": self.sub_type,
                "provider_name": settings.TITLE,
                "proxy_provider_url": self.user.clash_proxy_provider_endpoint,
            },
        )

    def get_clash_proxy_providers(self):
        """todo support multi provider group"""
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
            if node.enable_direct:
                node_configs.append(
                    {
                        "clash_config": node.get_user_clash_config(self.user),
                        "name": node.name,
                    }
                )
        for cfg_list in relay_node_group.values():
            node_configs.extend(cfg_list)
        # 添加将中转节点的 host 设置成直连规则
        return render_to_string(
            "clash/providers.yaml",
            {
                "nodes": node_configs,
                "relay_nodes_host": pm.RelayNode.get_active_relay_nodes_host_list(),
            },
        )
