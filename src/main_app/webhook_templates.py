import copy
import hashlib
import hmac
import random
import string
import time
import uuid
from functools import partial

from django.conf import settings


def sign_payload(payload):
    timestamp = payload["signature"]["timestamp"]
    token = payload["signature"]["token"]
    signature = hmac.new(
        key=settings.MOCK_MAILGUN_KEY.encode(),
        msg="{}{}".format(timestamp, token).encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()
    payload["signature"]["signature"] = signature


CLICKED = {
    "signature": {"token": "", "timestamp": "", "signature": ""},
    "event-data": {
        "id": "",
        "timestamp": None,
        "log-level": "info",
        "event": "clicked",
        "message": {"headers": {"message-id": ""}},
        "recipient": "alice@example.com",
        "recipient-domain": "example.com",
        "ip": "50.56.129.169",
        "geolocation": {"country": "US", "region": "CA", "city": "San Francisco"},
        "client-info": {
            "client-os": "Linux",
            "device-type": "desktop",
            "client-name": "Chrome",
            "client-type": "browser",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31",
        },
        "campaigns": [],
        "tags": [],
        "user-variables": {},
    },
}

DELIVERED = {
    "signature": {
        "token": "c7986654d1ef8a7023d5aeee28a8b3d4e274b284a2e2484c4b",
        "timestamp": "1639052591",
        "signature": "633664b5005d3ebd1e4c41e84c15e3e8991b9ed62b15b81650b50e60dfb2e03b",
    },
    "event-data": {
        "id": "CPgfbmQMTCKtHW6uIWtuVe",
        "timestamp": 1521472262.908181,
        "log-level": "info",
        "event": "delivered",
        "delivery-status": {
            "tls": True,
            "mx-host": "smtp-in.example.com",
            "code": 250,
            "description": "",
            "session-seconds": 0.4331989288330078,
            "utf8": True,
            "attempt-no": 1,
            "message": "OK",
            "certificate-verified": True,
        },
        "flags": {
            "is-routed": False,
            "is-authenticated": True,
            "is-system-test": False,
            "is-test-mode": False,
        },
        "envelope": {
            "transport": "smtp",
            "sender": "bob@sandboxaf8ff5f71f0c47e5aa3302448d999835.mailgun.org",
            "sending-ip": "209.61.154.250",
            "targets": "alice@example.com",
        },
        "message": {
            "headers": {
                "to": "Alice <alice@example.com>",
                "message-id": "20130503182626.18666.16540@sandboxaf8ff5f71f0c47e5aa3302448d999835.mailgun.org",
                "from": "Bob <bob@sandboxaf8ff5f71f0c47e5aa3302448d999835.mailgun.org>",
                "subject": "Test delivered webhook",
            },
            "attachments": [],
            "size": 111,
        },
        "recipient": "alice@example.com",
        "recipient-domain": "example.com",
        "storage": {
            "url": "https://se.api.mailgun.net/v3/domains/sandboxaf8ff5f71f0c47e5aa3302448d999835.mailgun.org/messages/message_key",
            "key": "message_key",
        },
        "campaigns": [],
        "tags": [],
        "user-variables": {"my_var_1": "Mailgun Variable #1", "my-var-2": "awesome"},
    },
}
OPENED = {
    "signature": {"token": "", "timestamp": None, "signature": ""},
    "event-data": {
        "id": "XXXXXX",
        "timestamp": 1521243339.873676,
        "log-level": "info",
        "event": "opened",
        "message": {"headers": {"message-id": ""}},
        "recipient": "",
        "recipient-domain": "",
        "ip": "1.1.1.1",
        "geolocation": {"country": "US", "region": "CA", "city": "San Francisco"},
        "client-info": {
            "client-os": "Linux",
            "device-type": "desktop",
            "client-name": "Chrome",
            "client-type": "browser",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31",
        },
        "campaigns": [],
        "tags": [],
        "user-variables": {},
    },
}

FAILED = {
    "signature": {"token": "", "timestamp": None, "signature": ""},
    "event-data": {
        "id": "G9Bn5sl1TC6nu79C8C0bwg",
        "timestamp": None,
        "log-level": "error",
        "event": "failed",
        "severity": "permanent",
        "reason": "suppress-bounce",
        "delivery-status": {
            "attempt-no": 1,
            "message": "",
            "code": 605,
            "description": "Not delivering to previously bounced address",
            "session-seconds": 0,
        },
        "flags": {
            "is-routed": False,
            "is-authenticated": True,
            "is-system-test": False,
            "is-test-mode": False,
        },
        "envelope": {"sender": "", "transport": "smtp", "targets": ""},
        "message": {
            "headers": {"to": "", "message-id": "", "from": "", "subject": ""},
            "attachments": [],
            "size": 111,
        },
        "recipient": "",
        "recipient-domain": "",
        "storage": {"url": "", "key": ""},
        "campaigns": [],
        "tags": [],
        "user-variables": {},
    },
}

COMPLAINED = {
    "signature": {"token": "", "timestamp": "1639003724", "signature": ""},
    "event-data": {
        "id": "xxxx",
        "timestamp": None,
        "log-level": "warn",
        "event": "complained",
        "envelope": {"sending-ip": "1.1.1.1"},
        "flags": {"is-test-mode": False},
        "message": {
            "headers": {"to": "", "message-id": "", "from": "", "subject": ""},
            "attachments": [],
            "size": 111,
        },
        "recipient": "",
        "campaigns": [],
        "tags": [],
        "user-variables": {},
    },
}

FAILURE_TEMPORARY = {
    "signature": {"token": "", "timestamp": "", "signature": ""},
    "event-data": {
        "id": "xxx",
        "timestamp": None,
        "log-level": "warn",
        "event": "failed",
        "reason": "generic",
        "severity": "temporary",
        "delivery-status": {
            "attempt-no": 1,
            "certificate-verified": True,
            "code": 452,
            "description": "",
            "message": "4.2.2 The email account that you tried to reach is over quota. Please direct\n4.2.2 the recipient to\n4.2.2  https://support.example.com/mail/?p=422",
            "mx-host": "smtp-in.example.com",
            "retry-seconds": 600,
            "session-seconds": 0.1281740665435791,
            "tls": True,
            "utf8": True,
        },
        "flags": {
            "is-authenticated": True,
            "is-routed": False,
            "is-system-test": False,
            "is-test-mode": False,
        },
        "envelope": {
            "sender": "",
            "transport": "smtp",
            "targets": "",
            "sending-ip": "1.1.1.1",
        },
        "message": {
            "attachments": [],
            "headers": {"message-id": "", "from": "", "to": "", "subject": ""},
            "size": 111,
        },
        "recipient": "",
        "recipient-domain": "",
        "storage": {"key": "message_key", "url": ""},
        "campaigns": [],
        "tags": [],
        "user-variables": {},
    },
}

UNSUBSCRIBED = {
    "signature": {"token": "", "timestamp": "", "signature": ""},
    "event-data": {
        "id": "xxx",
        "timestamp": None,
        "log-level": "info",
        "event": "unsubscribed",
        "message": {"headers": {"message-id": ""}},
        "recipient": "",
        "recipient-domain": "",
        "ip": "1.1.1.1",
        "geolocation": {"country": "US", "region": "CA", "city": "San Francisco"},
        "client-info": {
            "client-os": "Linux",
            "device-type": "desktop",
            "client-name": "Chrome",
            "client-type": "browser",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31",
        },
        "campaigns": [],
        "tags": [],
        "user-variables": {},
    },
}


def render(template, message, recipient, domain):
    working_template = copy.copy(template)
    timestamp = time.time()
    email_address = recipient.address
    full_email_address = recipient.display_address
    email_address_domain = email_address.split("@")[1]

    working_template["event-data"]["id"] = str(uuid.uuid4())
    working_template["event-data"]["timestamp"] = timestamp
    working_template["event-data"]["user-variables"] = message.json_variables
    working_template["event-data"]["message"]["headers"][
        "from"
    ] = message.from_field.display_address
    working_template["event-data"]["message"]["headers"]["to"] = full_email_address
    working_template["event-data"]["message"]["headers"]["subject"] = message.subject
    working_template["event-data"]["message"]["headers"]["message-id"] = (
        str(message.pk) + "@" + domain.name
    )
    working_template["event-data"]["message"]["headers"]["size"] = 100
    working_template["event-data"]["recipient"] = email_address
    working_template["event-data"]["recipient-domain"] = email_address_domain
    working_template["event-data"]["id"] = str(uuid.uuid4())
    try:
        working_template["event-data"]["storage"]["key"] = str(message.pk)
        working_template["event-data"]["storage"]["url"] = (
            f"http://localhost/v3/domains/" f"{domain.name}/messages/{str(message.pk)}"
        )
    except KeyError:
        pass
    try:
        working_template["event-data"]["envelope"]["sending-ip"] = "1.1.1.1"
        working_template["event-data"]["envelope"]["targets"] = email_address
        working_template["event-data"]["envelope"]["targets"] = email_address

        working_template["event-data"]["envelope"][
            "sender"
        ] = message.from_field.address
    except KeyError:
        pass
    working_template["signature"]["timestamp"] = str(int(timestamp))
    working_template["signature"]["token"] = "".join(
        random.choices(string.ascii_letters + string.digits, k=50)
    )
    sign_payload(working_template)
    return working_template


WEBHOOKS = {
    "delivered": partial(render, DELIVERED),
    "clicks": partial(render, CLICKED),
    "opened": partial(render, OPENED),
    "unsubscribed": partial(render, UNSUBSCRIBED),
    "failed_temporary": partial(render, FAILURE_TEMPORARY),
    "failed": partial(render, FAILED),
    "complained": partial(render, COMPLAINED),
}
