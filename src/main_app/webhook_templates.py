import copy
import time
CLICKED = {"signature": {
    "token": "",
    "timestamp": "",
    "signature": ""},
    "event-data": {
        "id": "",
        "timestamp": None,
        "log-level": "info",
        "event": "clicked",
        "message": {
            "headers": {
                "message-id": ""
            }
        },
        "recipient": "alice@example.com",
        "recipient-domain": "example.com",
        "ip": "50.56.129.169",
        "geolocation": {
            "country": "US",
            "region": "CA",
            "city": "San Francisco"
        },
        "client-info": {
            "client-os": "Linux",
            "device-type": "desktop",
            "client-name": "Chrome",
            "client-type": "browser",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31"
        },
        "campaigns": [],
        "tags": [],
        "user-variables": {
        }
    }
}

DELIVERED = {"signature": {
    "token": "000000",
    "timestamp": "1639006661",
    "signature": "0ff0c50cc29b76cb6a17ce54bb55ce08089050ffed08a1d4979b6212fb19551d"},
             "event-data": {
                 "id": "xxxx",
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
                     "certificate-verified": True
                 },
                 "flags": {
                     "is-routed": False,
                     "is-authenticated": True,
                     "is-system-test": False,
                     "is-test-mode": False
                 },
                 "envelope": {
                     "transport": "smtp",
                     "sender": "bob@sandboxaf8ff5f71f0c47e5aa3302448d999835.mailgun.org",
                     "sending-ip": "209.61.154.250",
                     "targets": "alice@example.com"
                 },
                 "message": {
                     "headers": {
                         "to": "Alice <alice@example.com>",
                         "message-id": "20130503182626.18666.16540@sandboxaf8ff5f71f0c47e5aa3302448d999835.mailgun.org",
                         "from": "Bob <bob@sandboxaf8ff5f71f0c47e5aa3302448d999835.mailgun.org>",
                         "subject": "Test delivered webhook"
                     },
                     "attachments": [],
                     "size": 111
                 },
                 "recipient": "alice@example.com",
                 "recipient-domain": "example.com",
                 "storage": {
                     "url": "https://mock-gun.api/",
                     "key": "message_key"
                 },
                 "campaigns": [],
                 "tags": [],
                 "user-variables": {
                 }
             }}
OPENED = {"signature": {"token": "", "timestamp": None, "signature": ""},
          "event-data": {
              "id": "XXXXXX",
              "timestamp": 1521243339.873676,
              "log-level": "info",
              "event": "opened",
              "message": {
                  "headers": {
                      "message-id": ""
                  }
              },
              "recipient": "",
              "recipient-domain": "",
              "ip": "1.1.1.1",
              "geolocation": {
                  "country": "US",
                  "region": "CA",
                  "city": "San Francisco"
              },
              "client-info": {
                  "client-os": "Linux",
                  "device-type": "desktop",
                  "client-name": "Chrome",
                  "client-type": "browser",
                  "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31"
              },
              "campaigns": [],
              "tags": [],
              "user-variables": {
              }
          }}

FAILED = {"signature": {"token": "", "timestamp": None, "signature": ""},
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
                  "session-seconds": 0
              },
              "flags": {
                  "is-routed": False,
                  "is-authenticated": True,
                  "is-system-test": False,
                  "is-test-mode": False
              },
              "envelope": {
                  "sender": "",
                  "transport": "smtp",
                  "targets": ""
              },
              "message": {
                  "headers": {
                      "to": "",
                      "message-id": "",
                      "from": "",
                      "subject": ""
                  },
                  "attachments": [],
                  "size": 111
              },
              "recipient": "",
              "recipient-domain": "",
              "storage": {
                  "url": "",
                  "key": ""
              },
              "campaigns": [],
              "tags": [],
              "user-variables": {
              }
          }}

COMPLAINED = {
    "signature": {"token": "", "timestamp": "1639003724", "signature": ""},
    "event-data": {
        "id": "xxxx",
        "timestamp": None,
        "log-level": "warn",
        "event": "complained",
        "envelope": {
            "sending-ip": "1.1.1.1"
        },
        "flags": {
            "is-test-mode": False
        },
        "message": {
            "headers": {
                "to": "",
                "message-id": "",
                "from": "",
                "subject": ""
            },
            "attachments": [],
            "size": 111
        },
        "recipient": "",
        "campaigns": [],
        "tags": [],
        "user-variables": {
        }
    }}

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
            "utf8": True
        },
        "flags": {
            "is-authenticated": True,
            "is-routed": False,
            "is-system-test": False,
            "is-test-mode": False
        },
        "envelope": {
            "sender": "",
            "transport": "smtp",
            "targets": "",
            "sending-ip": "1.1.1.1"
        },
        "message": {
            "attachments": [],
            "headers": {
                "message-id": "",
                "from": "",
                "to": "",
                "subject": ""
            },
            "size": 111
        },
        "recipient": "",
        "recipient-domain": "",
        "storage": {
            "key": "message_key",
            "url": ""
        },
        "campaigns": [],
        "tags": [],
        "user-variables": {
        }
    }}

UNSUBSCRIBED = {"signature": {"token": "", "timestamp": "", "signature": ""},
                "event-data": {
                    "id": "xxx",
                    "timestamp": None,
                    "log-level": "info",
                    "event": "unsubscribed",
                    "message": {
                        "headers": {
                            "message-id": ""
                        }
                    },
                    "recipient": "",
                    "recipient-domain": "",
                    "ip": "1.1.1.1",
                    "geolocation": {
                        "country": "US",
                        "region": "CA",
                        "city": "San Francisco"
                    },
                    "client-info": {
                        "client-os": "Linux",
                        "device-type": "desktop",
                        "client-name": "Chrome",
                        "client-type": "browser",
                        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31"
                    },
                    "campaigns": [],
                    "tags": [],
                    "user-variables": {
                    }
                }}



DELIVERED = {"signature": {
    "token": "000000",
    "timestamp": "1639006661",
    "signature": "0ff0c50cc29b76cb6a17ce54bb55ce08089050ffed08a1d4979b6212fb19551d"},
             "event-data": {
                 "id": "xxxx",
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
                     "certificate-verified": True
                 },
                 "flags": {
                     "is-routed": False,
                     "is-authenticated": True,
                     "is-system-test": False,
                     "is-test-mode": False
                 },
                 "envelope": {
                     "transport": "smtp",
                     "sender": "bob@sandboxaf8ff5f71f0c47e5aa3302448d999835.mailgun.org",
                     "sending-ip": "209.61.154.250",
                     "targets": "alice@example.com"
                 },
                 "message": {
                     "headers": {
                         "to": "Alice <alice@example.com>",
                         "message-id": "20130503182626.18666.16540@sandboxaf8ff5f71f0c47e5aa3302448d999835.mailgun.org",
                         "from": "Bob <bob@sandboxaf8ff5f71f0c47e5aa3302448d999835.mailgun.org>",
                         "subject": "Test delivered webhook"
                     },
                     "attachments": [],
                     "size": 111
                 },
                 "recipient": "alice@example.com",
                 "recipient-domain": "example.com",
                 "storage": {
                     "url": "https://mock-gun.api/",
                     "key": "message_key"
                 },
                 "campaigns": [],
                 "tags": [],
                 "user-variables": {
                 }
             }}

def render_delivered(message):
    working_template = copy.copy(DELIVERED)
    timestamp = time.time()
    working_template['signature']['timestamp'] = str(int(timestamp))
    event_data = working_template['event_data']
    
    working_template['signature']['timestamp'] = str(int(timestamp))

