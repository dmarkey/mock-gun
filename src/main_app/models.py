import random
import string
import uuid

from django.db import models
from main_app.webhook_templates import WEBHOOKS

# Create your models here.


class MockGunDomain(models.Model):
    internal_id = models.CharField(max_length=64, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    is_disabled = models.BooleanField(default=False)
    name = models.CharField(max_length=512, primary_key=True)
    require_tls = models.BooleanField(default=False)
    skip_verification = models.BooleanField(default=True)
    type = models.CharField(default="sandbox", max_length=512)
    smtp_login = models.CharField(default="postmaster@samples.mockgun.org",
                                  max_length=512)
    web_prefix = models.CharField(default="email", max_length=512)
    web_scheme = models.CharField(default="http", max_length=10)
    wildcard = models.BooleanField(default=False)
    state = models.CharField(default="active", max_length=64, choices=[
        ("active", "active"),
        ("unverified", "unverified"),
        ("disabled", "disabled"),
    ])

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.internal_id:
            self.internal_id = ''.join(random.choices(string.ascii_letters
                                                      + string.digits, k=24))
        super().save(*args, **kwargs)


class EmailAddress(models.Model):
    address = models.CharField(primary_key=True, max_length=1024)
    display_address = models.CharField(max_length=1024)

    def __str__(self):
        return self.address


class Template(models.Model):
    template = models.TextField()
    name = models.CharField(max_length=256, primary_key=True)
    description = models.CharField(max_length=256)
    version = models.CharField(max_length=256, default="v1.0")


class MockGunMessage(models.Model):
    to = models.ManyToManyField(EmailAddress, related_name="to")
    from_field = models.ForeignKey(EmailAddress, related_name="from_field",
                                   on_delete=models.CASCADE)
    cc = models.ManyToManyField(EmailAddress, related_name="cc", blank=True)
    bcc = models.ManyToManyField(EmailAddress, related_name="bcc",
                                 blank=True)
    subject = models.CharField(max_length=512)
    text = models.TextField(default="", blank=True)
    html = models.TextField(default="", blank=True)
    tag = models.CharField(max_length=512, blank=True)
    template = models.ForeignKey(Template, null=True,
                                 on_delete=models.CASCADE, blank=True)
    domain = models.ForeignKey(MockGunDomain, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    raw_payload = models.JSONField()
    json_variables = models.JSONField()

    def send_mock_webhooks(self):
        for hook in self.domain.mockwebhook_set.all():
            hook.send_for_message(self)

    def __str__(self):
        to = ",".join(self.to.all().values_list("address", flat=True))
        return f"{to} - {self.subject}"


class MockWebhook(models.Model):
    delay = models.IntegerField(default=1)
    url = models.URLField()
    domain = models.ForeignKey(MockGunDomain, on_delete=models.CASCADE)
    ssl_verify = models.BooleanField(default=False)
    webhook_type = models.CharField(max_length=128, choices=[
        ("opened", "Opens"),
        ("clicks", "Clicks"),
        ("delivered", "Delivered Messages"),
        ("failed", "Permanent Failure"),
        ("complained", "Spam Complaint"),
        ("failed_temporary", "Temporary Failure"),
        ("unsubscribed", "Unsubscribed"),
    ])

    def send_for_message(self, message):
        for to in message.to.all():
            WEBHOOKS[self.webhook_type](message, to, message.domain)

    def __str__(self):
        return f"{self.domain.name}:{self.webhook_type} - {self.url}"
