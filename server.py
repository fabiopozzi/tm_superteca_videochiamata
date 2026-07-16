import json
import logging
import os
from flask import Flask, request, make_response
from firebase_admin import credentials, db, initialize_app, messaging
from firebase_admin.exceptions import FirebaseError

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("st4")

_SENSITIVE_KEYS = {"jwt", "fcmToken", "token"}


def _redact(value):
    """Return a log-safe copy: sensitive values masked, structures recursed."""
    if isinstance(value, dict):
        return {k: ("***" + str(v)[-4:] if k in _SENSITIVE_KEYS else _redact(v))
                for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value


# Initialize Firebase Realtime Database
def initialize_firebase():
    try:
        # Replace with the path to your Service Account Key JSON file
        cred = credentials.Certificate("st4-videocall.json")
        # Replace with your Firebase Realtime Database URL
        initialize_app(cred, {
            'databaseURL':  'https://st4-videocall-default-rtdb.europe-west1.firebasedatabase.app'
        })
        log.info("Successfully connected to Firebase Realtime Database!")
    except Exception as e:
        log.error("Error initializing Firebase: %s", e)
        exit()

app = Flask(__name__)
initialize_firebase()

@app.route("/bacheche")
def bacheche():
    ref = db.reference('/bacheche')
    b = ref.get()
    log.debug("Bacheche: %s", _redact(b))
    return b if b else {}


@app.route("/all")
def tutto():
    ref = db.reference('/')
    b = ref.get()
    log.debug("TUTTO: %s", _redact(b))
    return b if b else {}


@app.route("/bacheca/<string:id>")
def bacheca(id):
    path = f"/bacheche/{id}"
    ref = db.reference(path)
    result = ref.get()
    if not result:
        result = {}
    return result


@app.route("/devices")
def devices():
    ref = db.reference('/devices')
    d = ref.get()
    log.debug("Periferiche: %s", _redact(d))
    return d if d else {}


@app.route("/device/<string:nome>")
def device(nome):
    path = f"/devices/{nome}"
    ref = db.reference(path)
    result = ref.get()
    if not result:
        result = {}
    return result


@app.route("/notify", methods=['POST'])
def notify():
    log.debug("notify payload: %s", _redact(request.json))
    if 'matricola' not in request.json.keys():
        return make_response({}, 400)
    if 'jwt' not in request.json.keys():
        return make_response({}, 400)
    if 'http' not in request.json.keys():
        return make_response({}, 400)

    matricola = request.json['matricola']
    log.info("notify matricola: %s", matricola)

    r = bacheca(matricola)
    if 'devices' not in r:
        log.warning("matricola errata o inesistente: %s", matricola)
        return make_response({'errore': 'matricola errata o inesistente'}, 400)

    lista_devices = r['devices']
    if not lista_devices:
        log.warning("nessun device associato alla matricola: %s", matricola)
        return make_response({'errore': 'nessun device associato alla matricola'}, 400)
    device_name = list(lista_devices)[0]
    log.info("notify device: %s", device_name)

    device_data = device(device_name)
    if not device_data or 'fcmToken' not in device_data:
        log.warning("id device errato o senza fcmToken: %s", _redact(device_data))
        return make_response({'errore': 'id device errato o non esistente'}, 400)

    registration_token = device_data['fcmToken']

    message = messaging.Message(
        token=registration_token,
        data={
            'url': request.json['http'],
            'room': 'NomeStanzaTest',
            'jwt': request.json['jwt'],
            'caller_name': 'Dr. Mario Rossi',
        },
        android=messaging.AndroidConfig(
            priority='high',
        ),
        apns=messaging.APNSConfig(
            headers={
                'apns-priority': '10',
                'apns-topic': 'com.latecnomedica.st4videocall',
                'apns-push-type': 'alert',
            },
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    sound='ringtone.aiff',
                    content_available=True,
                    mutable_content=True,
                    category='INCOMING_CALL_CATEGORY',
                ),
            ),
        ),
    )
    log.debug("sending FCM to device %s (room=%s)", device_name, 'NomeStanzaTest')
    # JSON effettivamente serializzato e inviato a FCM (stesso encoder di messaging.send)
    log.debug(
        "FCM outgoing JSON: %s",
        json.dumps(
            _redact(messaging._MessagingService.encode_message(message)),
            ensure_ascii=False,
            indent=2,
        ),
    )

    try:
        response = messaging.send(message)
        # Response is a message ID string.
        log.info("Successfully sent message: %s", response)
    except ValueError as e:
        log.warning("MESSAGGIO NON VALIDO: %s", e)
        return make_response({'result': 'FAILURE', 'errore': 'messaggio non valido'}, 400)
    except FirebaseError as e:
        log.error("ERRORE INVIO [%s]: %s", e.code, e)
        return make_response({'result': 'FAILURE'}, 502)

    return {'result': 'SUCCESS'}



@app.route("/new_device", methods=['POST'])
def new_device():
    if 'nome' not in request.json.keys():
        return make_response({}, 400)
    if 'dati' not in request.json.keys():
        return make_response({}, 400)

    nome = request.json['nome']
    dati = request.json['dati']
    path = f"/devices/{nome}"
    ref = db.reference(path)
    ref.update(dati)

    log.info("Data successfully written to Firebase: %s", path)
    return make_response({}, 200)


@app.route("/new_bacheca", methods=['POST'])
def new_bacheca():
    if 'nome' not in request.json.keys():
        return make_response({}, 400)
    if 'dati' not in request.json.keys():
        return make_response({}, 400)

    nome = request.json['nome']
    dati = request.json['dati']
    path = f"/bacheche/{nome}"
    ref = db.reference(path)
    ref.update(dati)

    log.info("Data successfully written to Firebase: %s", path)
    return make_response({}, 200)
