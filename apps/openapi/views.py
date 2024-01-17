from django.http import JsonResponse
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet

from apps.ext import lock
from apps.openapi.serializer import ProxyNodeSerializer, UserInfoSerializer
from apps.openapi.utils import OpenAPIStaffAuthentication, gen_common_error_response
from apps.proxy.models import ProxyNode
from apps.sspanel.models import UserCheckInLog, UserSocialProfile


class BaseOpenAPIViewSet(ModelViewSet):
    authentication_classes = [OpenAPIStaffAuthentication]


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


class UserViewSet(BaseOpenAPIViewSet):
    serializer_class = UserInfoSerializer
    queryset = UserInfoSerializer.Meta.model.objects.all()

    @action(detail=True, methods=["get"])
    def info(self, request, pk):
        user = self.get_object()
        return JsonResponse(self.serializer_class(user).data)

    @action(detail=True, methods=["post"])
    def checkin(self, request, pk):
        user = self.get_object()
        with lock.user_checkin_lock(user.pk):
            if user.today_is_checkin:
                return gen_common_error_response("today is checkin")
            log = UserCheckInLog.checkin(user)
            data = {
                "user_id": user.pk,
                "checkin_time": log.date,
                "increased_traffic": log.increased_traffic,
            }
            return JsonResponse(data=data)

    @action(detail=False, methods=["post"])
    def search(self, request):
        platform = request.data.get("platform")
        platform_user_id = request.data.get("platform_user_id")
        if not platform or not platform_user_id:
            return gen_common_error_response(
                "platform and platform_user_id in body is required"
            )
        up = UserSocialProfile.get_by_platform_user_id(platform, platform_user_id)
        if not up:
            return gen_common_error_response(
                f"user with platform:{platform} platform_user_id:{platform_user_id} not found",
                status=404,
            )
        return JsonResponse(self.serializer_class(up.user).data)
