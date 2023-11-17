from rest_framework import serializers

from apps.proxy.models import ProxyNode


class ProxyNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProxyNode
        fields = "__all__"

    multi_user_port = serializers.SerializerMethodField()

    def get_multi_user_port(self, node: ProxyNode):
        return node.get_user_port()
