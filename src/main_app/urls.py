from django.urls import path, include
from rest_framework import routers


from main_app import views
from main_app.views import MockGunMessageViewset, MockGunEmailValidateView

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'domains', views.MockGunDomainViewset)

urlpatterns = [
    path('v3/<str:domain>/messages', MockGunMessageViewset.as_view({"post": "create"})),
    path('v3/', include(router.urls)),
    path('v4/address/validate',MockGunEmailValidateView.as_view({"post": "create", "get": "create"})),
]