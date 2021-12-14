from django.urls import path
from django.views.generic import RedirectView
from main_app.views import (
    MockGunMessageViewset,
    MockGunEmailValidateView,
    DataImportExportView,
    TemplatesView,
    TemplateVersionsView,
    MockGunDomainViewset,
)


urlpatterns = [
    path("v3/domains", MockGunDomainViewset.as_view({"get": "list"})),
    path(
        "v3/domains/<str:domain>",
        MockGunDomainViewset.as_view({"get": "get"}),
    ),
    path("v3/<str:domain>/messages", MockGunMessageViewset.as_view({"post": "create"})),
    path(
        "v3/<str:domain>/templates",
        TemplatesView.as_view({"post": "create", "get": "list"}),
    ),
    path(
        "v3/<str:domain>/templates/<str:template_name>/versions/<str:version>",
        TemplateVersionsView.as_view({"get": "get"}),
    ),
    path(
        "v3/<str:domain>/templates/<str:template_name>/versions",
        TemplateVersionsView.as_view({"get": "list"}),
    ),
    path(
        "v3/<str:domain>/templates/<str:template_name>",
        TemplatesView.as_view({"get": "get"}),
    ),
    path(
        "v4/address/validate",
        MockGunEmailValidateView.as_view({"post": "create", "get": "create"}),
    ),
    path("data", DataImportExportView.as_view({"post": "create", "get": "get"})),
    path(
        "", RedirectView.as_view(url="/admin/main_app/mockgunmessage/", permanent=False)
    ),
]
