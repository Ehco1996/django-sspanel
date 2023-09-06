from django.forms import model_to_dict
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.openapi.utils import gen_common_error_response, openapi_authorized
from apps.proxy.models import ProxyNode
from apps.utils import handle_json_request


class ProxyNodeSearchView(View):
    @csrf_exempt
    @method_decorator(openapi_authorized)
    def dispatch(self, *args, **kwargs):
        return super(ProxyNodeSearchView, self).dispatch(*args, **kwargs)

    def get(self, request):
        ip = request.GET.get("ip")
        if not ip:
            return gen_common_error_response("ip in query is required")

        node = ProxyNode.get_by_ip(ip)
        if not node:
            return gen_common_error_response(
                f"node with ip:{ip}  not found", status=404
            )
        return JsonResponse(model_to_dict(node))


class ProxyNodeDetailView(View):
    @csrf_exempt
    @method_decorator(openapi_authorized)
    @method_decorator(handle_json_request)
    def dispatch(self, *args, **kwargs):
        return super(ProxyNodeDetailView, self).dispatch(*args, **kwargs)

    def patch(self, request, node_id):
        node = ProxyNode.get_by_id(node_id)
        if not node:
            return gen_common_error_response(
                f"node with id:{node_id}  not found", status=404
            )
        enable = request.json.get("enable")
        node.enable = enable
        node.save()
        return JsonResponse(model_to_dict(node))
