from collections import defaultdict

from django.conf import settings
from django.template.loader import render_to_string


class UserSubManager:
    """统一管理用户的订阅"""

    SUB_TYPE_NORMAL = "NORMAL"
    SUB_TYPE_CLASH = "clash"
    SUB_TYPE_CLASH_PRO = "clash_pro"

    SUB_TYPES_SET = {
        SUB_TYPE_NORMAL,
        SUB_TYPE_CLASH,
        SUB_TYPE_CLASH_PRO,
    }

    def __init__(self, user, sub_type, node_list):
        self.user = user
        if sub_type not in self.SUB_TYPES_SET:
            sub_type = self.SUB_TYPE_NORMAL
        self.sub_type = sub_type
        self.node_list = node_list

    def get_sub_info(self):
        if self.sub_type in [self.SUB_TYPE_CLASH, self.SUB_TYPE_CLASH_PRO]:
            return self.get_clash_sub_yaml()
        return self.get_clash_proxy_providers()

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
        return render_to_string(
            "clash/providers.yaml",
            {"nodes": node_configs},
        )
