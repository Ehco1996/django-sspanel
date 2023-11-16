from django.http import JsonResponse
from django.views import View

from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

from apps.openapi.utils import gen_common_error_response
from apps.proxy.models import ProxyNode


class ProxyNodeViewSet(ViewSet):
    @action(detail=False, methods=["post"])
    def get(self, request):
        ip = request.GET.get("ip")
        if not ip:
            return gen_common_error_response("ip in query is required")

        node = ProxyNode.get_by_ip(ip)
        if not node:
            return gen_common_error_response(
                f"node with ip:{ip}  not found", status=404
            )
        return JsonResponse(node.to_openapi_dict())

    def patch(self, request, node_id):
        node = ProxyNode.get_by_id(node_id)
        if not node:
            return gen_common_error_response(
                f"node with id:{node_id}  not found", status=404
            )
        enable = request.json.get("enable")
        node.enable = enable
        node.save()
        return JsonResponse(node.to_openapi_dict())


class ProxyNodeResetMultiUserPortView(View):
    def post(self, request, node_id):
        node = ProxyNode.get_by_id(node_id)
        if not node:
            return gen_common_error_response(
                f"node with id:{node_id}  not found", status=404
            )
        node.reset_random_multi_user_port()
        return JsonResponse(node.to_openapi_dict())
