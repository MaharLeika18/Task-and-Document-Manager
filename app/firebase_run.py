from flask import request
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import dotenv
import time

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
        decoded_token = verify_id_token_with_retry(id_token)
        return decoded_token
    except:
        return None


def verify_id_token_with_retry(id_token, max_attempts=3, retry_delay=1):
    last_exception = None
    for attempt in range(1, max_attempts + 1):
        try:
            return auth.verify_id_token(id_token)
        except Exception as e:
            last_exception = e
            message = str(e).lower()
            if 'token used too early' in message and attempt < max_attempts:
                time.sleep(retry_delay)
                continue
            raise
    raise last_exception