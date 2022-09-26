from collections import defaultdict
from decimal import Decimal

from django.conf import settings
from django.template.loader import render_to_string


class UserSubManager:
    """统一管理用户的订阅"""

    CLIENT_SHADOWROCKET = "shadowrocket"
    CLIENT_CLASH = "clash"
    CLIENT_CLASH_PREMIUM = "clash_premium"
    CLIENT_CLASH_PROXY_PROVIDER = "clash_proxy_provider"

    CLIENT_SET = {
        CLIENT_SHADOWROCKET,
        CLIENT_CLASH,
        CLIENT_CLASH_PREMIUM,
        CLIENT_CLASH_PROXY_PROVIDER,
    }

    def __init__(self, user, sub_client, node_list):
        self.user = user
        if sub_client not in self.CLIENT_SET:
            sub_client = self.CLIENT_CLASH_PROXY_PROVIDER
        self.sub_client = sub_client
        self.node_list = node_list

    def _get_clash_sub_yaml(self):
        return render_to_string(
            "clash/main.yaml",
            {
                "sub_client": self.sub_client,
                "provider_name": settings.TITLE,
                "proxy_provider_url": self.user.clash_proxy_provider_endpoint,
            },
        )

    def _get_shadowrocket_sub_links(self):
        sub_links = ""
        relay_node_group = defaultdict(list)
        for node in self.node_list:
            if node.enable_relay:
                for rule in node.relay_rules.filter(relay_node__enable=True):
                    relay_node_group[rule.relay_node].append(
                        node.get_user_shadowrocket_sub_link(self.user, rule)
                    )
            if node.enable_direct:
                sub_links += node.get_user_shadowrocket_sub_link(self.user) + "\n"

        for sub_link_list in relay_node_group.values():
            for link in sub_link_list:
                sub_links += link + "\n"
        return sub_links

    def get_sub_info(self):
        if self.sub_client in [self.CLIENT_CLASH, self.CLIENT_CLASH_PREMIUM]:
            return self._get_clash_sub_yaml()
        elif self.sub_client == self.CLIENT_SHADOWROCKET:
            return self._get_shadowrocket_sub_links()
        else:
            return self.get_clash_proxy_providers()

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
                name = node.name
                if node.enlarge_scale != Decimal(1.0):
                    name += f"-{node.enlarge_scale}倍"
                node_configs.append(
                    {
                        "clash_config": node.get_user_clash_config(self.user),
                    }
                )
        for cfg_list in relay_node_group.values():
            node_configs.extend(cfg_list)
        return render_to_string(
            "clash/providers.yaml",
            {"nodes": node_configs},
        )
