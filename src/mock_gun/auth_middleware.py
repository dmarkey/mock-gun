from django.conf import settings
from django.http import JsonResponse
import base64

from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.shortcuts import redirect

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
        if request.path in ("", "/"):
            return redirect("/admin/main_app/mockgunmessage/")
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
            print(f"REQUEST:{request.build_absolute_uri()}")
            resp = get_response(request)
            print(f"RESPONSE:{resp.content}")
            return resp

        return JsonResponse({"message": "Invalid private key"})

    return middleware
