from django.db.models.signals import pre_delete, post_save
from apps.ssserver.models import Node, Suser


def clear_node_user_configs_cache(sender, instance, created, *args, **kwargs):
    Suser.clear_get_user_configs_by_node_id_cache(node_ids=[instance.node_id])


def register_connectors():
    post_save.connect(clear_node_user_configs_cache, sender=Node)
    pre_delete.connect(clear_node_user_configs_cache, sender=Node)

