def migrate_ss_node():
    from apps.sspanel.models import SSNode
    from apps.ssserver.models import Node

    for node in Node.objects.filter(ss_type=0):
        SSNode.objects.create(
            node_id=node.node_id,
            enable=bool(node.show),
            level=node.level,
            custom_method=node.custom_method,
            name=node.name,
            info=node.info,
            country=node.country,
            server=node.server,
            method=node.method,
            used_traffic=node.used_traffic,
            total_traffic=node.total_traffic,
        )
        print(f"miggrate node_id {node.node_id} down!")


if __name__ == "__main__":
    from importlib import import_module

    import_module("__init__", "commands")
    migrate_ss_node()
