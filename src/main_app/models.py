import random
import string
import uuid
import threading
import time

from django.db import models
from main_app.webhook_templates import WEBHOOKS
import requests


# Create your models here.


def send_webhook(delay, url, payload, verify):
    time.sleep(delay)
    print(payload)
    resp = requests.post(url, json=payload, verify=verify)
    resp.raise_for_status()
    print(f"Webhook to {url} sent successfully")


def queue_webhook(delay, url, payload, verify):
    thread = threading.Thread(target=send_webhook, args=[delay, url, payload, verify])
    thread.start()


class MockGunDomain(models.Model):
    internal_id = models.CharField(max_length=64, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    is_disabled = models.BooleanField(default=False)
    name = models.CharField(max_length=512, primary_key=True)
    require_tls = models.BooleanField(default=False)
    skip_verification = models.BooleanField(default=True)
    type = models.CharField(default="sandbox", max_length=512)
    smtp_login = models.CharField(
        default="postmaster@samples.mockgun.org", max_length=512
    )
    web_prefix = models.CharField(default="email", max_length=512)
    web_scheme = models.CharField(default="http", max_length=10)
    wildcard = models.BooleanField(default=False)
    state = models.CharField(
        default="active",
        max_length=64,
        choices=[
            ("active", "active"),
            ("unverified", "unverified"),
            ("disabled", "disabled"),
        ],
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.internal_id:
            self.internal_id = "".join(
                random.choices(string.ascii_letters + string.digits, k=24)
            )
        super().save(*args, **kwargs)


class EmailAddress(models.Model):
    address = models.CharField(primary_key=True, max_length=1024)
    display_address = models.CharField(max_length=1024)

    def __str__(self):
        return self.address


class Template(models.Model):
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=256)
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    domain = models.ForeignKey(MockGunDomain, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.domain.name} - {self.name}"

    class Meta:
        ordering = ["created_at"]


class TemplateVersion(models.Model):
    version = models.CharField(max_length=256)
    content = models.TextField()
    description = models.CharField(max_length=256)
    comment = models.CharField(max_length=256)
    active = models.BooleanField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    template = models.ForeignKey(Template, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.template}:{self.version}"


class MockGunMessage(models.Model):
    to = models.ManyToManyField(EmailAddress, related_name="to")
    from_field = models.ForeignKey(
        EmailAddress, related_name="from_field", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    cc = models.ManyToManyField(EmailAddress, related_name="cc", blank=True)
    bcc = models.ManyToManyField(EmailAddress, related_name="bcc", blank=True)
    subject = models.CharField(max_length=512)
    text = models.TextField(default="", blank=True)
    html = models.TextField(default="", blank=True)
    tag = models.CharField(max_length=512, blank=True)
    template = models.ForeignKey(
        Template, null=True, on_delete=models.CASCADE, blank=True
    )
    domain = models.ForeignKey(MockGunDomain, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    raw_payload = models.JSONField()
    json_variables = models.JSONField()

    def send_mock_webhooks(self, enabled_only=True):
        webhooks = self.domain.mockwebhook_set.all()
        if enabled_only:
            webhooks = webhooks.filter(enabled=True)
        for hook in webhooks:
            hook.send_for_message(self)

    def __str__(self):
        to = ",".join(self.to.all().values_list("address", flat=True))
        return f"{to} - {self.subject}"


class MockWebhook(models.Model):
    delay = models.IntegerField(default=1)
    url = models.URLField()
    domain = models.ForeignKey(MockGunDomain, on_delete=models.CASCADE)
    ssl_verify = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    webhook_type = models.CharField(
        max_length=128,
        choices=[
            ("opened", "Opens"),
            ("clicks", "Clicks"),
            ("delivered", "Delivered Messages"),
            ("failed", "Permanent Failure"),
            ("complained", "Spam Complaint"),
            ("failed_temporary", "Temporary Failure"),
            ("unsubscribed", "Unsubscribed"),
        ],
    )

    def send_for_message(self, message):
        for to in (
            list(message.to.all()) + list(message.cc.all()) + list(message.bcc.all())
        ):
            rendered = WEBHOOKS[self.webhook_type](message, to, message.domain)
            queue_webhook(self.delay, self.url, rendered, self.ssl_verify)

    def __str__(self):
        return f"{self.domain.name}:{self.webhook_type} - {self.url}"
