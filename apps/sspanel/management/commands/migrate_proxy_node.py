from django.core.management.base import BaseCommand

from apps.proxy import models as m
from apps.sspanel.models import RelayNode, SSNode, SSRelayRule


class Command(BaseCommand):
    def handle(self, *args, **options):

        # relay node old:new
        relay_node_map = {}
        for node in RelayNode.objects.all():
            relay_node_map[node.node_id] = m.RelayNode.objects.create(
                id=node.id,
                name=node.name,
                server=node.server,
                enable=node.enable,
                isp=node.isp,
            )
        print("sync 中转节点", relay_node_map)
        # ss node
        ss_node_map = {}
        for node in SSNode.objects.all():
            ss_node_map[node.node_id] = m.ProxyNode.objects.create(
                id=node.node_id,
                name=node.name,
                server=node.server,
                enable=node.enable,
                level=node.level,
                info=node.info,
                country=node.country,
                used_traffic=node.used_traffic,
                total_traffic=node.total_traffic,
                enlarge_scale=node.enlarge_scale,
                ehco_listen_host=node.ehco_listen_host,
                ehco_listen_port=node.ehco_listen_port,
                ehco_listen_type=node.ehco_listen_type,
                ehco_transport_type=node.ehco_transport_type,
            )
            m.SSConfig.objects.create(
                proxy_node=ss_node_map[node.node_id],
                method=node.method,
                multi_user_port=node.port,
            )
        print("sync ss节点", ss_node_map)
        # relay rule
        for rule in SSRelayRule.objects.all():
            m.RelayRule.objects.create(
                proxy_node=ss_node_map[rule.ss_node.node_id],
                relay_node=relay_node_map[rule.relay_node.node_id],
                relay_port=rule.relay_port,
                listen_type=rule.listen_type,
                transport_type=rule.transport_type,
            )
        print("sync ss node to new down")
