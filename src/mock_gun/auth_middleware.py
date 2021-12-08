from django.conf import settings
from django.http import JsonResponse
import base64


def check_incoming_key(encoded):
    if not encoded:
        return False
    return base64.b64decode(
        encoded.split("Basic ")[1]).decode() ==\
           f"api:{settings.MOCK_MAILGUN_KEY}"


def auth_middleware(get_response):

    def middleware(request):
        auth_header = request.headers.get('Authorization')

        if (request.user.is_authenticated or check_incoming_key(auth_header)
                or request.path.startswith("/admin")):
            return get_response(request)

        return JsonResponse({"message": "Invalid private key"})

    return middleware