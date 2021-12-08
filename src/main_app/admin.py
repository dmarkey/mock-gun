from django.contrib import admin
from main_app.models import EmailRepipient, Template,\
    MockGunDomain,MockGunMessage

# Register your models here.
admin.site.register(EmailRepipient)
admin.site.register(Template)
admin.site.register(MockGunDomain)
admin.site.register(MockGunMessage)
