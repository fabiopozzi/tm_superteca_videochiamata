# ST4 Videocall — Notification Backend

Small Flask backend that bridges an external caller to the ST4 videocall Flutter app
(`com.latecnomedica.st4videocall`). It reads/writes a Firebase Realtime Database and
sends FCM push notifications that trigger an incoming-call screen on registered devices.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Place the Firebase service-account key at `st4-videocall.json` in the project root
(loaded by `initialize_firebase()` in `server.py`).

## Run

```bash
flask --app server run                 # http://127.0.0.1:5000
flask --app server run --debug         # auto-reload
LOG_LEVEL=DEBUG flask --app server run  # verbose (redacted) logging
```

## Endpoints

| Method | Path                | Purpose                                            |
|--------|---------------------|----------------------------------------------------|
| GET    | `/all`              | Dump the whole database                            |
| GET    | `/bacheche`         | All boards                                          |
| GET    | `/bacheca/<id>`     | One board by matricola                              |
| GET    | `/devices`          | All devices                                         |
| GET    | `/device/<nome>`    | One device by name                                 |
| POST   | `/notify`           | Ring the first device of a board (see below)       |
| POST   | `/new_device`       | Upsert a device: `{"nome": ..., "dati": {...}}`     |
| POST   | `/new_bacheca`      | Upsert a board:  `{"nome": ..., "dati": {...}}`     |

`POST /notify` body: `{"matricola": ..., "jwt": ..., "http": ...}` — looks up the board
by `matricola`, takes the **first** device in its `devices` map, and sends an FCM
incoming-call push to that device's `fcmToken`.

## Notes

### Logging
- Uses the `logging` module; level via `LOG_LEVEL` env var (default `INFO`).
- `jwt`, `fcmToken`, and `token` values are **redacted** (masked to the last 4 chars)
  wherever they are logged, via the `_redact()` helper in `server.py`.
- Full DB dumps and request payloads log only at `DEBUG` (and stay redacted), so the
  default `INFO` level never emits them.

### FCM message shape
- Built with typed config classes (`AndroidConfig`, `APNSConfig`, …); raw dicts are
  rejected by `firebase_admin >= 7.x`.
- Android full-screen incoming-call behavior comes from the notification **channel**
  (`call_channel_v3`) on the app side — FCM's `AndroidNotification` has no
  `full_screen_intent`/`category` field (confirmed absent through 7.5.0).
- APNs uses the `INCOMING_CALL_CATEGORY` category at priority 10.

### Credentials
- `*.json` service-account keys are **secrets** and are gitignored — never commit them.
- The Realtime DB URL is currently hard-coded in `initialize_firebase()`.

### Deployment / trust model
- By design this service runs **locally on the endpoint that sends the request**, split
  out from the main app to decouple development of the two functionalities. The caller is
  co-located and trusted, so the endpoints have **no authentication** — this is
  intentional, not a gap.
- **Caveat:** this relies on binding to loopback only. Do **not** expose it on a public
  interface (`--host 0.0.0.0`) or a shared network without adding an auth layer first —
  `/all` returns every `fcmToken` and `/notify` can push a spoofed incoming call.

### Known limitations / TODO
- **`room` and `caller_name` are hard-coded** (`NomeStanzaTest` / `Dr. Mario Rossi`);
  they should come from the request payload.
- **Only the first device** of a board is notified; boards with multiple devices ring
  just one.
- Firebase keys cannot contain `. # $ [ ] /`; `nome`/`id` from requests are interpolated
  into DB paths without sanitization.

## Development

There are no automated tests. Endpoints are exercised manually with `curl`
(example payloads in `appunti.org`).
