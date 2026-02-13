import firebase_admin
from firebase_admin import credentials, firestore, auth
import os

cred = credentials.Certificate(os.environ.get("FIREBASE_ADMIN_FILE_PATH"))
firebase_admin.initialize_app(cred)

db = firestore.client()