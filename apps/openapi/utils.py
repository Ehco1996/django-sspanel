from functools import wraps

from django.http import JsonResponse

from apps.openapi.models import UserOpenAPIKey


def gen_common_error_response(msg: str, status=400) -> JsonResponse:
    return JsonResponse({"error_msg": msg}, status=status)


def openapi_authorized(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        key = request.META.get("HTTP_X_API_KEY", "")
        if not key:
            return gen_common_error_response(
                "x-api-key in header not found", status=401
            )
        user_key = UserOpenAPIKey.get_by_key(key)
        if not user_key:
            return gen_common_error_response("x-api-key is invalid", status=401)
        request.user = user_key.user
        return view_func(request, *args, **kwargs)

    return wrapper
