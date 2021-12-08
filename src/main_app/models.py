from django.db import models

# Create your models here.


class MockGunDomain(models.Model):
    id = models.UUIDField(primary_key=True)
    created_at = models.DateTimeField(auto_created=True)
    is_disabled = models.BooleanField(default=False)
    name = models.CharField(max_length=512)
    require_tls = models.BooleanField(default=False)
    skip_verification = models.BooleanField(default=True)
    type = models.CharField(default="sandbox", max_length=512)
    smtp_login = models.CharField(default="postmaster@samples.mockgun.org",
                                  max_length=512)
    web_prefix = models.CharField(default="email", max_length=512)
    web_scheme = models.CharField(default="http", max_length=10)
    wildcard = models.BooleanField(default=False)


class EmailRepipient(models.Model):
    address = models.EmailField()


class Template(models.Model):
    template = models.TextField()
    version = models.SmallIntegerField()


class MockGunMessage(models.Model):
    to = models.ManyToManyField(EmailRepipient, related_name="to")
    cc = models.ManyToManyField(EmailRepipient, related_name="cc")
    bcc = models.ManyToManyField(EmailRepipient, related_name="bcc")
    subject = models.CharField(max_length=512)
    text = models.TextField()
    html = models.TextField()
    tag = models.CharField(max_length=512)
    template = models.ForeignKey(Template, null=True, on_delete=models.CASCADE)
    raw_payload = models.JSONField





