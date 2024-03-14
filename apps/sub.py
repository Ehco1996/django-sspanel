import base64

from django.conf import settings
from django.template.loader import render_to_string

from apps.sspanel.models import User


class UserSubManager:
    """统一管理用户的订阅"""

    CLIENT_SHADOWROCKET = "shadowrocket"
    CLIENT_CLASH = "clash"
    CLIENT_CLASH_PROXY_PROVIDER = "clash_proxy_provider"

    CLIENT_SET = {
        CLIENT_SHADOWROCKET,
        CLIENT_CLASH,
        CLIENT_CLASH_PROXY_PROVIDER,
    }

    def __init__(self, user, node_list, sub_client=CLIENT_CLASH):
        self.user = user
        if sub_client in self.CLIENT_SET:
            self.sub_client = sub_client
        elif not sub_client or "clash" in sub_client:
            self.sub_client = self.CLIENT_CLASH
        else:
            raise ValueError(f"sub_client {sub_client} not support")

        self.node_list = node_list

    def _get_clash_sub_yaml(self):
        user: User = self.user
        user_proxy_provider_url = user.clash_proxy_provider_endpoint
        direct_ip_rule_set_url = user.direct_ip_rule_set_endpoint
        direct_domain_rule_set_url = user.direct_domain_rule_set_endpoint

        return render_to_string(
            "clash/main.yaml",
            {
                "sub_client": self.sub_client,
                "provider_name": settings.SITE_TITLE,
                "proxy_provider_url": user_proxy_provider_url,
                "direct_ip_rule_set_url": direct_ip_rule_set_url,
                "direct_domain_rule_set_url": direct_domain_rule_set_url,
            },
        )

    def _get_shadowrocket_sub_links(self):
        sub_links = ""
        # for clean the rule have the same port
        # key: relay_node_id+port, value: shadowrocket_sub_link
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
        if self.sub_client == self.CLIENT_CLASH:
            return self._get_clash_sub_yaml()
        elif self.sub_client == self.CLIENT_SHADOWROCKET:
            return self._get_shadowrocket_sub_links()
        elif self.sub_client == self.CLIENT_CLASH_PROXY_PROVIDER:
            return self.get_clash_proxy_providers()
        else:
            raise ValueError(f"sub_client {self.sub_client} not support")

    def get_clash_proxy_providers(self):
        """todo support multi provider group"""
        node_configs = []
        # for clean the rule have the same port
        # key: relay_node_id+port, value: clash cfg
        relay_node_group = {}
        for node in self.node_list:
            if node.enable_relay:
                for rule in node.get_enabled_relay_rules():
                    key = f"{rule.relay_node.id}{rule.relay_port}"
                    relay_node_group[key] = {
                        "clash_config": node.get_user_clash_config(self.user, rule),
                        "name": rule.name,
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
