from django.conf import settings
from django.http import JsonResponse
import base64

from django.contrib.auth import get_user_model
from django.contrib.auth import login

User = get_user_model()


def check_incoming_key(encoded):
    if not encoded:
        return False
    return (
        base64.b64decode(encoded.split("Basic ")[1]).decode()
        == f"api:{settings.MOCK_MAILGUN_KEY}"
    )


def auth_middleware(get_response):
    def middleware(request):
        auth_header = request.headers.get("Authorization")
        if request.path.startswith("/data"):
            return get_response(request)
        if request.path.startswith("/admin"):
            users = User.objects.filter(username="admin")
            if not users:
                user = User.objects.create_superuser(
                    "admin", "admin@mockgun.com", "password"
                )
            else:
                user = users[0]

            login(request, user)
            return get_response(request)

        if (
            request.user.is_authenticated
            or check_incoming_key(auth_header)
            or request.path.startswith("/admin")
        ):
            return get_response(request)

        return JsonResponse({"message": "Invalid private key"})

    return middleware
