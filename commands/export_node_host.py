def export_node_host():
    from apps.ssserver.models import Node

    hosts = []
    for node in Node.objects.all():
        hosts.append("'{}'".format(node.server))
    with open("node_host.txt", "w") as f:
        f.writelines("\n".join(hosts))
    print("export node host down ! node num: ", len(hosts))


if __name__ == "__main__":
    from importlib import import_module

    import_module("__init__", "commands")
    export_node_host()
