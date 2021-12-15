from django.contrib import admin
from django.db.models import JSONField

from django.contrib.auth.models import Group, User

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
admin.site.unregister(Group)
admin.site.unregister(User)


@admin.register(MockGunMessage)
class MockMessageAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {"widget": JSONEditorWidget},
    }
    list_display = ["id", "created_at", "from_field",
                    "subject", "template", "domain"]
    list_filter = ["domain", "subject"]
