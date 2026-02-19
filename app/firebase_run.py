from flask import request
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import dotenv

dotenv.load_dotenv()

cred = credentials.Certificate(os.getenv('FIREBASE_ADMIN_FILE_PATH'))
firebase_admin.initialize_app(cred)

db = firestore.client()

#check the token from the frontend and return the decoded token if valid, otherwise return None
def verify_firebase_token():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    id_token = auth_header.split(" ").pop()

    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except:
        return None