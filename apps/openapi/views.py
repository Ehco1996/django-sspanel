from django.http import JsonResponse
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet

from apps.openapi.serializer import ProxyNodeSerializer
from apps.openapi.utils import OpenAPIAuthentication, gen_common_error_response
from apps.proxy.models import ProxyNode


class BaseOpenAPIViewSet(ModelViewSet):
    authentication_classes = [OpenAPIAuthentication]


class ProxyNodeViewSet(BaseOpenAPIViewSet):
    serializer_class = ProxyNodeSerializer
    queryset = ProxyNode.objects.all()

    def list(self, request, *args, **kwargs):
        nodes = ProxyNode.objects.all()
        page = self.paginate_queryset(nodes)
        data = self.serializer_class(page, many=True).data
        return self.get_paginated_response(data)

    @action(detail=False, methods=["get"])
    def search(self, request):
        ip = request.GET.get("ip")
        if not ip:
            return gen_common_error_response("ip in query is required")

        node = ProxyNode.get_by_ip(ip)
        if not node:
            return gen_common_error_response(
                f"node with ip:{ip}  not found", status=404
            )
        return JsonResponse(self.serializer_class(node).data)

    @action(detail=True, methods=["post"])
    def reset_multi_user_port(self, request, pk):
        node = ProxyNode.get_by_id(pk)
        if not node:
            return gen_common_error_response(
                f"node with id:{pk}  not found", status=404
            )
        node.reset_random_multi_user_port()
        return JsonResponse(self.serializer_class(node).data)

    def partial_update(self, request, pk):
        node = ProxyNode.get_by_id(pk)
        if not node:
            return gen_common_error_response(
                f"node with id:{pk}  not found", status=404
            )
        enable = request.data.get("enable")
        node.enable = enable
        node.save()
        return JsonResponse(self.serializer_class(node).data)
