from django.db.models.signals import post_save, pre_delete, pre_save

from apps.ext import cache
from apps.sspanel import models as m


def set_user_pre_save_level(sender, instance, *args, **kwargs):
    old_user = m.User.get_or_none(instance.pk)
    if old_user:
        instance._pre_level = old_user.level


def clear_get_user_ss_configs_by_node_id_cache(sender, instance, *args, **kwargs):

    if isinstance(instance, m.SSNode):
        node_ids = [instance.node_id]
    elif isinstance(instance, m.User):
        node_ids = m.SSNode.get_node_ids_by_level(instance.level)
        if hasattr(instance, "_pre_level"):
            level = getattr(instance, "_pre_level")
            node_ids.extend(m.SSNode.get_node_ids_by_level(level))
            node_ids = set(node_ids)
    else:
        return

    keys = [
        m.SSNode.get_user_ss_configs_by_node_id.make_cache_key(m.SSNode, node_id)
        for node_id in node_ids
    ]
    cache.delete_many(keys)


def clear_get_user_vmess_configs_by_node_id_cache(sender, instance, *args, **kwargs):

    if isinstance(instance, m.User):
        node_ids = m.VmessNode.get_node_ids_by_level(instance.level)
        if hasattr(instance, "_pre_level"):
            level = getattr(instance, "_pre_level")
            node_ids.extend(m.VmessNode.get_node_ids_by_level(level))
            node_ids = set(node_ids)
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

    # set old user level before save
    pre_save.connect(set_user_pre_save_level, sender=m.User)

    # clear_get_user_ss_configs_by_node_id_cache
    post_save.connect(clear_get_user_ss_configs_by_node_id_cache, sender=m.User)
    pre_delete.connect(clear_get_user_ss_configs_by_node_id_cache, sender=m.User)
    post_save.connect(clear_get_user_ss_configs_by_node_id_cache, sender=m.SSNode)
    pre_delete.connect(clear_get_user_ss_configs_by_node_id_cache, sender=m.SSNode)

    # clear_get_user_vmess_configs_by_node_id_cache
    post_save.connect(clear_get_user_vmess_configs_by_node_id_cache, sender=m.User)
    pre_delete.connect(clear_get_user_vmess_configs_by_node_id_cache, sender=m.User)
    post_save.connect(clear_get_user_vmess_configs_by_node_id_cache, sender=m.VmessNode)
    pre_delete.connect(
        clear_get_user_vmess_configs_by_node_id_cache, sender=m.VmessNode
    )
