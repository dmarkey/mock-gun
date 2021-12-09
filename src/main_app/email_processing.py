from rest_framework.exceptions import ValidationError
import email
from validate_email import validate_email

from main_app.models import EmailAddress, MockGunMessage, Template


def validate_all_emails(emails):
    for x in emails:
        email_address = email.utils.parseaddr(x)[1]
        if validate_email(email_address, check_format=True,
                          check_blacklist=False,
                          check_dns=False, check_smtp=False) is not True:
            raise ValidationError({"message": f"{x} is not a valid email"})


def process_incoming_email(payload, domain):
    text = payload.get("text")
    html = payload.get("html")
    tag = payload.get("tag")
    template = payload.get("template")
    template_obj = None
    if template:
        template = template[0]
        try:
            template_obj = Template.objects.filter(name=template)[0]
        except IndexError:
            raise ValidationError(
                {"message":
                     f"template {template} does not exist *WARNING* "
                     f"Mailgun does not give this error in their API,"
                     f" it fails silently."})

    subject = payload.get("subject")
    if not text and not html:
        raise ValidationError({"message": "Need at least one of 'text'"
                                          " or 'html' parameters specified"})
    to_field = payload.get("to")
    from_field = payload.get("from")
    if from_field is None:
        raise ValidationError({"message": "from parameter is missing"})
    if to_field is None:
        raise ValidationError({"message": "to parameter is missing"})

    to = payload['to']
    bcc = payload.get("bcc", [])
    cc = payload.get("cc", [])
    from_field = payload.get("from")[0]

    all_emails = (to + bcc + cc + [from_field])

    validate_all_emails(all_emails)
    from_addr = EmailAddress.objects.get_or_create(
        address=email.utils.parseaddr(from_field)[1])[0]
    to_objects = [EmailAddress.objects.get_or_create(
        address=email.utils.parseaddr(x)[1])[0] for x in to_field]
    cc_objects = [EmailAddress.objects.get_or_create(
        address=email.utils.parseaddr(x)[1])[0] for x in cc]
    bcc_objects = [EmailAddress.objects.get_or_create(
        address=email.utils.parseaddr(x)[1])[0] for x in bcc]
    if not text:
        text = ""
    else:
        text = text[0]
    if not html:
        html = ""
    else:
        html = html[0]

    if not tag:
        tag = ""
    else:
        tag = tag[0]

    if not subject:
        subject = ""
    else:
        subject = subject[0]

    message = MockGunMessage()
    message.html = html
    message.raw_payload = payload
    message.text = text
    message.subject = subject
    message.domain = domain
    message.tag = tag
    message.template = template_obj
    message.from_field = from_addr
    message.save()
    message.to.set(to_objects)
    message.bcc.set(bcc_objects)
    message.cc.set(cc_objects)
    return message
