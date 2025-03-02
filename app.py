from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from firebase_admin import credentials, initialize_app, storage
import bcrypt
import jwt
import datetime
import json
import os

app = Flask(__name__)
CORS(app)

# MongoDB Configuration
mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['notehive']

# Firebase Storage Configuration
cred_dict = json.loads(os.getenv("FIREBASE_CREDENTIALS"))
cred = credentials.Certificate(cred_dict)
initialize_app(cred, {'storageBucket': 'notehive.appspot.com'})

# Secret Key for JWT Authentication
app.config['SECRET_KEY'] = 'your_secret_key_here'

# User Registration
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data['email']
    password = data['password'].encode('utf-8')
    if db.users.find_one({'email': email}):
        return jsonify({'message': 'User already exists'}), 400
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
    db.users.insert_one({'email': email, 'password': hashed_password})
    return jsonify({'message': 'User registered successfully'}), 201

# User Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data['email']
    password = data['password'].encode('utf-8')
    user = db.users.find_one({'email': email})
    if user and bcrypt.checkpw(password, user['password']):
        token = jwt.encode({'email': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)}, app.config['SECRET_KEY'])
        return jsonify({'token': token})
    return jsonify({'message': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(debug=True)
