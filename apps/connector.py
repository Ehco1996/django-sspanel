from django.db.models.signals import pre_delete, post_save
from apps.sspanel import models as m
from apps.utils import cache


def clear_get_user_ss_configs_by_node_id_cache(sender, instance, *args, **kwargs):

    if isinstance(instance, m.UserSSConfig):
        node_ids = m.SSNode.get_node_ids_by_level(instance.user.level)
    else:
        node_ids = [instance.node_id]

    keys = [
        m.SSNode.get_user_ss_configs_by_node_id.make_cache_key(m.SSNode, node_id)
        for node_id in node_ids
    ]
    cache.delete_many(keys)


def clear_user_get_by_pk_cache(sender, instance, *args, **kwargs):
    key = m.User.get_by_pk.make_cache_key(m.User, instance.pk)
    cache.delete(key)


def register_connectors():

    post_save.connect(clear_get_user_ss_configs_by_node_id_cache, sender=m.SSNode)
    pre_delete.connect(clear_get_user_ss_configs_by_node_id_cache, sender=m.SSNode)

    post_save.connect(clear_get_user_ss_configs_by_node_id_cache, sender=m.UserSSConfig)
    pre_delete.connect(
        clear_get_user_ss_configs_by_node_id_cache, sender=m.UserSSConfig
    )

    post_save.connect(clear_user_get_by_pk_cache, sender=m.User)
    pre_delete.connect(clear_user_get_by_pk_cache, sender=m.User)
