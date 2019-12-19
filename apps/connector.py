from django.db.models.signals import pre_delete, post_save
from apps.sspanel import models as m
from apps.ext import cache


def clear_user_get_by_pk_cache(sender, instance, *args, **kwargs):
    key = m.User.get_by_pk.make_cache_key(m.User, instance.pk)
    cache.delete(key)


def clear_get_user_ss_configs_by_node_id_cache(sender, instance, *args, **kwargs):

    if isinstance(instance, (m.UserSSConfig, m.UserTraffic)):
        user = m.User.get_by_pk(instance.user_id)
        node_ids = m.SSNode.get_node_ids_by_level(user.level)
    elif isinstance(instance, m.SSNode):
        node_ids = [instance.node_id]
    elif isinstance(instance, m.User):
        node_ids = m.SSNode.get_node_ids_by_level(instance.level)
    else:
        return

    keys = [
        m.SSNode.get_user_ss_configs_by_node_id.make_cache_key(m.SSNode, node_id)
        for node_id in node_ids
    ]
    cache.delete_many(keys)


def clear_get_user_vmess_configs_by_node_id(sender, instance, *args, **kwargs):

    if isinstance(instance, m.UserTraffic):
        user = m.User.get_by_pk(instance.user_id)
        node_ids = m.VmessNode.get_node_ids_by_level(user.level)
    elif isinstance(instance, m.VmessNode):
        node_ids = [instance.node_id]
    else:
        return
    keys = [
        m.VmessNode.get_user_vmess_configs_by_node_id.make_cache_key(
            m.VmessNode, node_id
        )
        for node_id in node_ids
    ]
    cache.delete_many(keys)


def register_connectors():
    # clear_user_get_by_pk_cache
    post_save.connect(clear_user_get_by_pk_cache, sender=m.User)
    pre_delete.connect(clear_user_get_by_pk_cache, sender=m.User)

    # clear_user_get_by_pk_cache
    post_save.connect(clear_get_user_ss_configs_by_node_id_cache, sender=m.SSNode)
    pre_delete.connect(clear_get_user_ss_configs_by_node_id_cache, sender=m.SSNode)

    post_save.connect(clear_get_user_ss_configs_by_node_id_cache, sender=m.UserSSConfig)
    pre_delete.connect(
        clear_get_user_ss_configs_by_node_id_cache, sender=m.UserSSConfig
    )

    post_save.connect(clear_user_get_by_pk_cache, sender=m.UserTraffic)
    pre_delete.connect(clear_user_get_by_pk_cache, sender=m.UserTraffic)

    # clear_get_user_vmess_configs_by_node_id
    post_save.connect(clear_get_user_vmess_configs_by_node_id, sender=m.VmessNode)
    pre_delete.connect(clear_get_user_vmess_configs_by_node_id, sender=m.VmessNode)

    post_save.connect(clear_get_user_vmess_configs_by_node_id, sender=m.UserTraffic)
    pre_delete.connect(clear_get_user_vmess_configs_by_node_id, sender=m.UserTraffic)
