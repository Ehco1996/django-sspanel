from django.http import JsonResponse
from rest_framework import authentication, exceptions

from apps.openapi.models import UserOpenAPIKey


class OpenAPIStaffAuthentication(authentication.TokenAuthentication):
    def valid_user(self, user):
        if not user.is_active or not user.is_staff or not user.is_superuser:
            return False
        return True

    def authenticate(self, request):
        key = request.META.get("HTTP_X_API_KEY", "")
        if not key:
            raise exceptions.NotAuthenticated("api key is required")
        user_key = UserOpenAPIKey.get_by_key(key)
        if not user_key:
            raise exceptions.AuthenticationFailed("api key is wrong", code=401)
        user = user_key.user
        if not self.valid_user(user):
            raise exceptions.AuthenticationFailed("user is not valid", code=401)
        return (user_key.user, None)


def gen_common_error_response(msg: str, status=400) -> JsonResponse:
    return JsonResponse({"error_msg": msg}, status=status)
