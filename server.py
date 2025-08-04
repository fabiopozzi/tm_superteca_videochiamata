import json
from flask import Flask, request, make_response
import firebase_admin
from firebase_admin import credentials, db

# Initialize Firebase Realtime Database
def initialize_firebase():
    try:
        # Replace with the path to your Service Account Key JSON file
        cred = credentials.Certificate("admin_sdk.json")
        # Replace with your Firebase Realtime Database URL
        firebase_admin.initialize_app(cred, {
            'databaseURL':  'https://prova-realtime-db-default-rtdb.europe-west1.firebasedatabase.app'
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


@app.route("/devices")
def devices():
    ref = db.reference('/devices')
    d = ref.get()
    print("Periferiche:", d)
    return d


@app.route("/new_device", methods=['POST'])
def new_device():
    if 'nome' not in request.json.keys():
        return make_response({}, 400)

    nome = request.json['nome']
    dati = request.json['dati']
    path = f"/devices/{nome}"
    ref = db.reference(path)
    ref.update(dati)

    print("Data successfully written to Firebase!")
    return make_response({}, 200)
