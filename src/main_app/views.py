import copy
import time
from io import StringIO
from urllib.parse import urlparse

from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import deserialize
from django.http import JsonResponse, HttpResponse
from rest_framework import serializers, viewsets
from rest_framework.exceptions import ValidationError
from validate_email import validate_email
from main_app.email_processing import process_incoming_email
from main_app.models import (
    MockGunDomain,
    MockGunMessage,
    Template,
    TemplateVersion,
    write_lock,
)
from django.core.management import call_command

# Cap on how long the wait endpoint may hold a connection open, so a
# forgotten/misconfigured test can't tie up a server thread indefinitely.
MAX_WAIT_TIMEOUT_SECONDS = 30
WAIT_POLL_INTERVAL_SECONDS = 0.25


class MockGunMessageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MockGunMessage
        fields = ["id"]


def serialize_message(message, include_body=False):
    data = {
        "id": str(message.pk),
        "created_at": message.created_at.strftime("%a, %d %b %Y %T UTC"),
        "domain": message.domain_id,
        "from": message.from_field.display_address or message.from_field.address,
        "to": list(message.to.all().values_list("display_address", flat=True)),
        "cc": list(message.cc.all().values_list("display_address", flat=True)),
        "bcc": list(message.bcc.all().values_list("display_address", flat=True)),
        "subject": message.subject,
        "tag": message.tag,
        "template": message.template.name if message.template_id else None,
    }
    if include_body:
        data["text"] = message.text
        data["html"] = message.html
        data["json_variables"] = message.json_variables
        data["raw_payload"] = message.raw_payload
    return data


def filter_messages(queryset, params):
    to = params.get("to")
    if to:
        queryset = queryset.filter(to__address=to)
    subject_contains = params.get("subject_contains")
    if subject_contains:
        queryset = queryset.filter(subject__icontains=subject_contains)
    tag = params.get("tag")
    if tag:
        queryset = queryset.filter(tag=tag)
    template = params.get("template")
    if template:
        queryset = queryset.filter(template__name=template)
    return queryset.distinct()


class MockGunDomainViewset(viewsets.ViewSet):
    def get(self, request, *args, **kwargs):
        try:
            domain = list(
                MockGunDomain.objects.filter(name=self.kwargs["domain"])
                .values(
                    "created_at",
                    "internal_id",
                    "is_disabled",
                    "name",
                    "require_tls",
                    "skip_verification",
                    "smtp_login",
                    "state",
                    "type",
                    "web_prefix",
                    "web_scheme",
                    "wildcard",
                )
                .values()
            )[0]
        except IndexError:
            return JsonResponse({"message": "Domain does not exist"}, status=404)
        domain["id"] = domain.pop("internal_id")
        domain["created_at"] = domain.pop("created_at").strftime("%a, %d %b %Y %T UTC")
        domain["receiving_dns_records"] = []
        domain["sending_dns_records"] = []
        return JsonResponse(domain)

    def list(self, request, *args, **kwargs):
        domains = list(
            MockGunDomain.objects.all()
            .values(
                "created_at",
                "internal_id",
                "is_disabled",
                "name",
                "require_tls",
                "skip_verification",
                "smtp_login",
                "state",
                "type",
                "web_prefix",
                "web_scheme",
                "wildcard",
            )
            .values()
        )
        for domain in domains:
            domain["id"] = domain.pop("internal_id")
            domain["created_at"] = domain.pop("created_at").strftime(
                "%a, %d %b %Y %T UTC"
            )

        return JsonResponse({"total_count": len(domains), "items": domains})


# Create your views here.
class MockGunMessageViewset(viewsets.ViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """

    def create(self, request, *args, **kwargs):
        try:
            domain = MockGunDomain.objects.get(name=self.kwargs["domain"])
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Domain does not exist"}, status=404)

        processed_payload = {x[0].lower(): x[1] for x in self.request.POST.lists()}
        json_variables = {
            x[0][2:]: x[1][0] for x in self.request.POST.lists() if x[0].startswith("v")
        }
        message = process_incoming_email(processed_payload, domain, json_variables)
        message.send_mock_webhooks()
        return JsonResponse(
            {"message": "Queued. Thank you.", "id": f"<{message.pk}@{domain.name}>"}
        )

    def list(self, request, *args, **kwargs):
        """Introspection: list messages captured for a domain, for QA/test use."""
        try:
            domain = MockGunDomain.objects.get(name=self.kwargs["domain"])
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Domain does not exist"}, status=404)

        messages = filter_messages(
            MockGunMessage.objects.filter(domain=domain), request.GET
        ).order_by("-created_at")

        limit = int(request.GET.get("limit", 50))
        offset = int(request.GET.get("offset", 0))
        total_count = messages.count()
        items = [serialize_message(m) for m in messages[offset : offset + limit]]

        return JsonResponse({"total_count": total_count, "items": items})

    def retrieve(self, request, *args, **kwargs):
        """Introspection: full body/headers of a single captured message."""
        try:
            domain = MockGunDomain.objects.get(name=self.kwargs["domain"])
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Domain does not exist"}, status=404)
        try:
            message = MockGunMessage.objects.get(
                domain=domain, pk=self.kwargs["message_id"]
            )
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Message does not exist"}, status=404)
        return JsonResponse(serialize_message(message, include_body=True))

    def destroy(self, request, *args, **kwargs):
        """Introspection: delete a single captured message."""
        try:
            domain = MockGunDomain.objects.get(name=self.kwargs["domain"])
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Domain does not exist"}, status=404)
        with write_lock:
            deleted, _ = MockGunMessage.objects.filter(
                domain=domain, pk=self.kwargs["message_id"]
            ).delete()
        if not deleted:
            return JsonResponse({"message": "Message does not exist"}, status=404)
        return JsonResponse({"message": "deleted"})

    def clear(self, request, *args, **kwargs):
        """Introspection: wipe all captured messages for a domain (test teardown)."""
        try:
            domain = MockGunDomain.objects.get(name=self.kwargs["domain"])
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Domain does not exist"}, status=404)
        with write_lock:
            queryset = MockGunMessage.objects.filter(domain=domain)
            deleted = queryset.count()
            queryset.delete()
        return JsonResponse({"message": "cleared", "deleted": deleted})

    def wait(self, request, *args, **kwargs):
        """
        Introspection: block until a message matching the given filters
        (to/subject_contains/tag/template) arrives, or `timeout` seconds
        elapse (default 10s, capped at MAX_WAIT_TIMEOUT_SECONDS). Lets test
        frameworks assert on async email delivery without a client-side
        poll loop.
        """
        try:
            domain = MockGunDomain.objects.get(name=self.kwargs["domain"])
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Domain does not exist"}, status=404)

        timeout = min(
            float(request.GET.get("timeout", 10)), MAX_WAIT_TIMEOUT_SECONDS
        )
        deadline = time.monotonic() + timeout

        while True:
            messages = filter_messages(
                MockGunMessage.objects.filter(domain=domain), request.GET
            ).order_by("-created_at")
            message = messages.first()
            if message:
                return JsonResponse(serialize_message(message, include_body=True))
            if time.monotonic() >= deadline:
                return JsonResponse(
                    {"message": "No matching message arrived in time"}, status=404
                )
            time.sleep(WAIT_POLL_INTERVAL_SECONDS)


# Create your views here.
class MockGunEmailValidateView(viewsets.ViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """

    TEMPLATE = {
        "address": "nonexistentemail@example.com",
        "is_disposable_address": False,
        "is_role_address": False,
        "reason": [],
        "result": "deliverable",
        "risk": "low",
    }

    def create(self, request, *args, **kwargs):
        address = request.data.get("address")
        if not address:
            raise ValidationError({"message": "no address given"})
        response = copy.copy(self.TEMPLATE)
        response["address"] = address
        if not validate_email(address):
            response["result"] = "undeliverable"
            response["risk"] = "high"

        return JsonResponse(response)


class DataImportExportView(viewsets.ViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """

    def create(self, request, *args, **kwargs):
        for obj in deserialize("json", request.body):
            obj.save()
        return HttpResponse("OK")

    def get(self, request, *args, **kwargs):
        out = StringIO()
        call_command(
            "dumpdata",
            "main_app.MockGunDomain",
            "main_app.Template",
            "main_app.MockWebhook",
            "main_app.TemplateVersion",
            stdout=out,
        )
        return HttpResponse(out.getvalue(), content_type="application/json")


class TemplatesView(viewsets.ViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """

    def create_template_version(self, template, content, tag, comment):
        tv = TemplateVersion()
        tv.description = ""
        tv.template = template
        tv.active = True
        tv.content = content
        tv.version = tag
        tv.comment = comment
        tv.save()

    def prepare_template(self, template):
        template["createdAt"] = template.pop("created_at").strftime(
            "%a, %d %b %Y %T UTC"
        )
        template["createdBy"] = ""
        template["id"] = str(template["id"])

    def get(self, request, *args, **kwargs):
        try:
            domain = MockGunDomain.objects.get(name=self.kwargs["domain"])
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Domain does not exist"}, status=404)
        templates = Template.objects.filter(
            domain=domain, name=self.kwargs["template_name"]
        ).values("description", "created_at", "id", "name")

        if not templates.exists():
            return JsonResponse({"message": "Template does not exist"}, status=404)
        template = templates[0]
        self.prepare_template(template)
        return JsonResponse(template)

    def list(self, request, *args, **kwargs):
        try:
            domain = MockGunDomain.objects.get(name=self.kwargs["domain"])
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Domain does not exist"}, status=404)
        limit = int(request.GET.get("limit", 100))
        page = request.GET.get("page", "first")
        p = request.GET.get("p", None)

        templates = list(
            Template.objects.filter(domain=domain).values(
                "description", "created_at", "id", "name"
            )
        )

        position = 0
        if page == "last":
            position = len(templates) - page
        elif page in ("previous", "next"):
            paginate_postition = 0
            for num, template in enumerate(templates):
                if template["name"] == p:
                    paginate_postition = num
            if page == "previous":
                position = paginate_postition - limit - 1
            if page == "next":
                position = paginate_postition + 1

        if position < 0:
            position = 0

        templates = templates[position:limit]
        templates_output = []

        for template in templates:
            self.prepare_template(template)
            templates_output.append(template)
        res = urlparse(self.request.build_absolute_uri())
        base_path = f"{res.scheme}://{res.hostname}:{res.port}{res.path}"
        try:
            next_name = templates[-1]["name"]
        except IndexError:
            next_name = ""
        try:
            previous_name = templates[0]["name"]
        except IndexError:
            previous_name = ""
        paging = {
            "first": f"{base_path}?limit={limit}",
            "next": f"{base_path}?page=next&limit={limit}&p={next_name}",
            "previous": f"{base_path}?page=previous&limit={limit}&p={previous_name}",
            "last": f"{base_path}?page=last&limit={limit}",
        }
        output = {"items": templates_output, "paging": paging}
        return JsonResponse(output)

    def create(self, request, *args, **kwargs):
        try:
            domain = MockGunDomain.objects.get(name=self.kwargs["domain"])
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Domain does not exist"}, status=404)
        name = request.data.get("name", None)
        description = request.data.get("descriptipn", "")
        template = request.data.get("template", "")
        template_tag = request.data.get("tag", "latest")
        comment = request.data.get("comment", "comment")
        if not name:
            raise ValidationError({"message": "Missing mandatory parameter: name"})

        if Template.objects.filter(name=name):
            raise ValidationError({"message": f"template {name} already exists"})

        t = Template()
        t.name = name
        t.description = description
        t.domain = domain
        t.save()
        if template:
            self.create_template_version(t, template_tag, template_tag, comment)

        return JsonResponse(
            {
                "message": "template has been stored",
                "template": {
                    "name": t.name,
                    "description": t.description,
                    "createdAt": t.created_at.strftime("%a, %d %b %Y %T UTC"),
                    "createdBy": "",
                    "id": str(t.pk),
                },
            }
        )


class TemplateVersionsView(TemplatesView):
    """
    API endpoint that allows groups to be viewed or edited.
    """

    def get(self, request, *args, **kwargs):
        try:
            domain = MockGunDomain.objects.get(name=self.kwargs["domain"])
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Domain does not exist"}, status=404)
        templates = Template.objects.filter(
            domain=domain, name=self.kwargs["template_name"]
        ).values("description", "created_at", "id", "name")

        if not templates.exists():
            return JsonResponse({"message": "Template does not exist"}, status=404)
        template = templates[0]
        template_version = TemplateVersion.objects.filter(
            template=template["id"], version=self.kwargs["version"]
        )
        if not template_version.exists():
            return JsonResponse(
                {"message": "Template version does not exist"}, status=404
            )
        template_version = template_version[0]
        self.prepare_template(template)
        version = {}
        version["createdAt"] = template_version.created_at.strftime(
            "%a, %d %b %Y %T UTC"
        )
        version["engine"] = "handlebars"
        version["tag"] = template_version.version
        version["comment"] = template_version.comment
        template["version"] = version
        return JsonResponse(template)

    def list(self, request, *args, **kwargs):
        try:
            domain = MockGunDomain.objects.get(name=self.kwargs["domain"])
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Domain does not exist"}, status=404)
        limit = int(request.GET.get("limit", 100))

        templates = Template.objects.filter(
            domain=domain, name=self.kwargs["template_name"]
        ).values("description", "created_at", "id", "name")

        if not templates.exists():
            return JsonResponse({"message": "Template does not exist"})
        template = templates[0]
        template_versions = list(
            TemplateVersion.objects.filter(template=template["id"]).values(
                "version", "created_at", "comment"
            )
        )

        page = request.GET.get("page", "first")
        p = request.GET.get("p", None)

        position = 0
        if page == "last":
            position = len(template_versions) - page
        elif page in ("previous", "next"):
            paginate_postition = 0
            for num, template_version in enumerate(template_versions):
                if template_version["version"] == p:
                    paginate_postition = num
            if page == "previous":
                position = paginate_postition - limit - 1
            if page == "next":
                position = paginate_postition + 1

        if position < 0:
            position = 0

        template_versions = template_versions[position:limit]
        template_version_output = []

        for template_version in template_versions:
            template_version["createdAt"] = template_version.pop("created_at").strftime(
                "%a, %d %b %Y %T UTC"
            )
            template_version["tag"] = template_version.pop("version")
            template_version["engine"] = "handlebars"

            template_version_output.append(template_version)
        res = urlparse(self.request.build_absolute_uri())
        base_path = f"{res.scheme}://{res.hostname}:{res.port}{res.path}"
        try:
            next_name = template_versions[-1]["tag"]
        except IndexError:
            next_name = ""
        try:
            previous_name = template_versions[0]["tag"]
        except IndexError:
            previous_name = ""
        paging = {
            "first": f"{base_path}?limit={limit}",
            "next": f"{base_path}?page=next&limit={limit}&p={next_name}",
            "previous": f"{base_path}?page=previous&limit={limit}&p={previous_name}",
            "last": f"{base_path}?page=last&limit={limit}",
        }
        self.prepare_template(template)
        template["versions"] = template_version_output
        output = {"template": template, "paging": paging}
        return JsonResponse(output)
