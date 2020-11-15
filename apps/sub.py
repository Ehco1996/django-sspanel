import base64

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
    SUB_TYPES = (
        (SUB_TYPE_SS, "只订阅SS"),
        (SUB_TYPE_VLESS, "只订阅Vless"),
        (SUB_TYPE_TROJAN, "只订阅Trojan"),
        (SUB_TYPE_CLASH, "通过Clash订阅所有"),
        (SUB_TYPE_CLASH_PRO, "通过ClashPro订阅所有"),
    )

    def __init__(self, user, sub_type):
        self.user = user
        if sub_type not in self.SUB_TYPES_SET:
            sub_type = self.SUB_TYPE_SS
        self.sub_type = sub_type
        self.node_list = self._fill_fake_node()

    def _fill_fake_node(self):
        """根据用户信息拿出所有需要的node
            - TODO 增加用户 等级，流量使用百分比,官网地址 的虚拟节点
        """
        return pm.ProxyNode.get_active_nodes(level=self.user.level)

    def get_clash_sub_links(self):
        node_configs = []
        for node in self.node_list:
            if node.enable_relay:
                for rule in node.relay_rules.filter(relay_node__enable=True):
                    node_configs.append(
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
        return render_to_string(
            "yamls/clash.yml", {"nodes": node_configs, "sub_type": self.sub_type}
        )

    def get_normal_sub_links(self):
        sub_links = ""
        for node in self.node_list:
            if node.enable_relay:
                for rule in node.relay_rules.filter(relay_node__enable=True):
                    sub_links += node.get_user_node_link(self.user, rule) + "\n"
            else:
                sub_links += node.get_user_node_link(self.user) + "\n"
        sub_links = base64.urlsafe_b64encode(sub_links.encode()).decode()
        return sub_links

    def get_sub_links(self):
        if self.sub_type in [self.SUB_TYPE_CLASH, self.SUB_TYPE_CLASH_PRO]:
            return self.get_clash_sub_links()
        return self.get_normal_sub_links()
