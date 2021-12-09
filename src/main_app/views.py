import copy

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from rest_framework import serializers, viewsets
from rest_framework.exceptions import ValidationError
from validate_email import validate_email
from main_app.email_processing import process_incoming_email
from main_app.models import MockGunDomain, MockGunMessage


class MockGunDomainSerializer(serializers.HyperlinkedModelSerializer):
    spam_action = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    def get_spam_action(self, obj):
        return "disabled"

    def get_created_at(self, obj):
        return obj.created_at.strftime("%a, %d %b %Y %T UTC")

    def get_id(self, obj):
        return obj.internal_id

    class Meta:
        model = MockGunDomain
        fields = ['id', 'created_at', 'name', 'require_tls',
                  "skip_verification", "smtp_login", "spam_action", "state",
                  "type", "web_prefix", "web_scheme", "wildcard"]


class MockGunMessageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MockGunMessage
        fields = ['id']


class MockGunDomainViewset(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = MockGunDomain.objects.all()
    serializer_class = MockGunDomainSerializer


# Create your views here.
class MockGunMessageViewset(viewsets.ViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """

    def create(self, request, *args, **kwargs):
        try:
            domain = MockGunDomain.objects.get(
                name=self.kwargs['domain'])
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Domain does not exist"},
                                status=404)

        processed_payload = {x[0].lower(): x[1]
                             for x in self.request.POST.lists()}
        message = process_incoming_email(processed_payload, domain)
        message.send_mock_webhooks()
        return JsonResponse({
            "message": "Queued. Thank you.",
            "id": f"<{message.pk}@{domain.name}>"
        })


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
        "risk": "low"
    }

    def create(self, request, *args, **kwargs):
        address = request.data.get("address")
        if not address:
            raise ValidationError({'message': "no address given"})
        response = copy.copy(self.TEMPLATE)
        response['address'] = address
        if not validate_email(address):
            response['result'] = "undeliverable"
            response['risk'] = "high"

        return JsonResponse(response)
