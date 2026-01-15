import json
from flask import Flask, request, make_response
from firebase_admin import credentials, db, initialize_app, messaging
from firebase_admin.exceptions import FirebaseError

# Initialize Firebase Realtime Database
def initialize_firebase():
    try:
        # Replace with the path to your Service Account Key JSON file
        cred = credentials.Certificate("st4-videocall.json")
        # Replace with your Firebase Realtime Database URL
        initialize_app(cred, {
            'databaseURL':  'https://st4-videocall-default-rtdb.europe-west1.firebasedatabase.app'
        })
        print("Successfully connected to Firebase Realtime Database!")
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        exit()

app = Flask(__name__)
initialize_firebase()

@app.route("/bacheche")
def bacheche():
    ref = db.reference('/bacheche')
    b = ref.get()
    print("Bacheche:", b)
    return b


@app.route("/all")
def tutto():
    ref = db.reference('/')
    b = ref.get()
    print("TUTTO:", b)
    return b


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
    print("Periferiche:", d)
    return d


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
    print(request.json)
    if 'matricola' not in request.json.keys():
        return make_response({}, 400)
    if 'jwt' not in request.json.keys():
        return make_response({}, 400)

    matricola = request.json['matricola']
    print(matricola)

    r = bacheca(matricola)
    if 'devices' not in r:
        print("matricola errata o inesistente")
        return make_response({'errore': 'matricola errata o inesistente'}, 400)

    lista_devices = r['devices']
    #print(lista_devices.keys())
    device_name = list(lista_devices)[0]
    print(device_name)

    device_data = device(device_name)
    if not device_data or 'fcmToken' not in device_data:
        print(device_data)
        print("ID ERRATO")
        return make_response({'errore': 'id device errato o non esistente'}, 400)

    registration_token = device_data['fcmToken']

    message = messaging.Message(
        data={
            'url': request.json['http'],
            'jwt': request.json['jwt'],
        },
        token=registration_token,
    )
    print(message)

    try:
        response = messaging.send(message)
        # Response is a message ID string.
        print('Successfully sent message:', response)
    except FirebaseError as e:
        print("ERRORE INVIO")
        print(e.code)
        print(e)
        return {'result': 'FAILURE'}

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

    print("Data successfully written to Firebase!")
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

    print("Data successfully written to Firebase!")
    return make_response({}, 200)
