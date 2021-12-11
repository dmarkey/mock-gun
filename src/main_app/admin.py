from django.contrib import admin
from django.db.models import JSONField

from main_app.models import (
    EmailAddress,
    Template,
    TemplateVersion,
    MockGunDomain,
    MockGunMessage,
    MockWebhook,
)
from django_json_widget.widgets import JSONEditorWidget

# Register your models here.
admin.site.register(EmailAddress)
admin.site.register(Template)
admin.site.register(TemplateVersion)
admin.site.register(MockGunDomain)
admin.site.register(MockWebhook)


@admin.register(MockGunMessage)
class MockMessageAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {"widget": JSONEditorWidget},
    }
