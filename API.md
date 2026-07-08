# mock-gun API reference

mock-gun is a Mailgun-compatible mock server: it accepts the same "send message"
calls a real app would send to Mailgun, stores them instead of delivering real
email, and fires configured webhooks (delivered/opened/clicked/etc). It also
exposes a JSON introspection API so QA agents and test frameworks can query,
wait for, and clear captured messages during a test run.

The server runs threaded and is safe to hit from parallel test workers
(e.g. pytest-xdist): writes are internally serialized so concurrent sends
never race SQLite, and reads (list/retrieve/wait) are never blocked by an
in-flight write.

## Auth

Every endpoint except `/admin` and `/data` requires HTTP Basic auth:

- username: `api`
- password: the `MOCK_MAILGUN_KEY` env var (defaults to 32 zero-padded digits prefixed with `key-` — see `mock_gun/settings.py`)

```
curl -u api:$MOCK_MAILGUN_KEY http://localhost:8000/v3/...
```

Unauthenticated requests get `{"message": "Invalid private key"}` with a 200
status (this matches the container's existing behavior — check the response
body, not just the status code).

## Sending a mock email (Mailgun-compatible)

`POST /v3/<domain>/messages` — form-encoded, same fields as Mailgun's send API:
`from`, `to`, `cc`, `bcc`, `subject`, `text`, `html`, `tag`, `template`, `v:<name>`
(template variables). Stores the message and queues any enabled webhooks for
that domain.

```
curl -u api:$KEY -X POST http://localhost:8000/v3/test.mockgun.org/messages \
  --data-urlencode "from=App <app@test.mockgun.org>" \
  --data-urlencode "to=alice@example.com" \
  --data-urlencode "subject=Welcome" \
  --data-urlencode "text=Hi there"
```

## Introspection API (for QA agents / test frameworks)

Everything below reads or clears what mock-gun has captured — use it in tests
to assert on emails your app under test sent, instead of scraping the Django
admin UI.

### List messages

`GET /v3/<domain>/messages`

Query params (all optional, combinable):

| param | meaning |
|---|---|
| `to` | exact recipient address |
| `subject_contains` | case-insensitive substring match on subject |
| `tag` | exact tag match |
| `template` | exact template name match |
| `limit` | page size (default 50) |
| `offset` | page offset (default 0) |

Returns `{"total_count": N, "items": [...]}`, newest first. Items are summaries
(no `text`/`html`/`raw_payload` — use retrieve for the full body).

### Get one message

`GET /v3/<domain>/messages/<id>`

Full detail: `to`, `cc`, `bcc`, `from`, `subject`, `tag`, `template`, `text`,
`html`, `json_variables`, `raw_payload`, `created_at`.

### Wait for a message

`GET /v3/<domain>/messages/wait`

Same filter params as list (`to`, `subject_contains`, `tag`, `template`), plus
`timeout` in seconds (default 10, capped at 30). Blocks until a matching
message arrives and returns it (full detail, like retrieve), or 404s with
`{"message": "No matching message arrived in time"}` once the timeout elapses.

Use this instead of a client-side poll loop when your test triggers an
async email send and then needs to assert on it:

```
curl -u api:$KEY "http://localhost:8000/v3/test.mockgun.org/messages/wait?to=alice@example.com&subject_contains=Welcome&timeout=15"
```

### Delete a message

`DELETE /v3/<domain>/messages/<id>` — removes one captured message.

### Clear all messages for a domain

`DELETE /v3/<domain>/messages` — wipes every captured message for the domain.
Use this in test teardown/setup so message queries in one test don't see
leftovers from another. Returns `{"message": "cleared", "deleted": N}`.

## Other endpoints

- `GET /v3/domains` / `GET /v3/domains/<name>` — list/get mock domains
- `POST /v4/address/validate` — mock Mailgun's address validation API
- `POST /v3/<domain>/templates`, `GET /v3/<domain>/templates[/<name>[/versions[/<version>]]]` — template CRUD/listing
- `GET/POST /data` — dump/load Django fixtures for domains, templates, and webhooks (unauthenticated by design, used for test fixture setup)
- `/admin` — Django admin UI (auto-provisions `admin`/`password` on first hit)
