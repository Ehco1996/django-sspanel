from django.http import JsonResponse
from redis.lock import LockError


class ErrorHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, LockError):
            return JsonResponse({"msg": exception.args[0]})
