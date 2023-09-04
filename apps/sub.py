import base64

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

    def _get_delay_url(self):
        return settings.HOST + f"/api/delay"

    def _get_clash_sub_yaml(self):
        return render_to_string(
            "clash/main.yaml",
            {
                "sub_client": self.sub_client,
                "provider_name": settings.TITLE,
                "proxy_provider_url": self.user.clash_proxy_provider_endpoint,
                "check_delay_url": self._get_delay_url(),
            },
        )

    def _get_shadowrocket_sub_links(self):
        sub_links = ""
        # for clean the rule have the same port
        # key: relay_node_id+port, value: cfg
        relay_node_group = {}
        for node in self.node_list:
            if node.enable_relay:
                for rule in node.get_enabled_relay_rules():
                    key = f"{rule.relay_node.id}{rule.relay_port}"
                    relay_node_group[key] = node.get_user_shadowrocket_sub_link(
                        self.user, rule
                    )
            if node.enable_direct:
                sub_links += node.get_user_shadowrocket_sub_link(self.user) + "\n"

        for link in relay_node_group.values():
            sub_links += link + "\n"
        sub_links = base64.urlsafe_b64encode(sub_links.encode()).decode()
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
        # for clean the rule have the same port
        # key: relay_node_id+port, value: cfg
        relay_node_group = {}
        for node in self.node_list:
            if node.enable_relay:
                for rule in node.get_enabled_relay_rules():
                    key = f"{rule.relay_node.id}{rule.relay_port}"
                    relay_node_group[key] = {
                        "clash_config": node.get_user_clash_config(self.user, rule),
                        "name": rule.remark,
                    }

            if node.enable_direct:
                node_configs.append(
                    {
                        "clash_config": node.get_user_clash_config(self.user),
                        "name": node.remark,
                    }
                )
        for cfg in relay_node_group.values():
            node_configs.append(cfg)
        return render_to_string(
            "clash/providers.yaml",
            {"nodes": sorted(node_configs, key=lambda x: x["name"])},
        )
