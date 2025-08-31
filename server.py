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
