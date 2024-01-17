from rest_framework import serializers

from apps.proxy.models import ProxyNode
from apps.sspanel.models import User


def get_proxy_node_exclude_fields():
    fields = ProxyNode._meta.fields
    field_names_with_ehco = [
        field.name for field in fields if field.name.startswith("ehco_")
    ]
    return field_names_with_ehco


class ProxyNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProxyNode
        exclude = get_proxy_node_exclude_fields()

    multi_user_port = serializers.SerializerMethodField()
    online_info = serializers.SerializerMethodField()

    def get_multi_user_port(self, node: ProxyNode):
        return node.get_user_port()

    def get_online_info(self, node: ProxyNode):
        return node.online_info


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # only show safe fields
        fields = [
            "id",
            "username",
            "balance",
            "level",
            "level_expire_time",
            "upload_traffic",
            "download_traffic",
            "total_traffic",
            "last_use_time",
        ]
