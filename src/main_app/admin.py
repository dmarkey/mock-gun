from django.contrib import admin
from main_app.models import EmailAddress, Template,\
    MockGunDomain, MockGunMessage, WebhookType, WebhookTarget

# Register your models here.
admin.site.register(EmailAddress)
admin.site.register(Template)
admin.site.register(MockGunDomain)
admin.site.register(MockGunMessage)
admin.site.register(WebhookType)
admin.site.register(WebhookTarget)
