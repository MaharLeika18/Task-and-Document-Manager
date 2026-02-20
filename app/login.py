# hello_app/views.py
from flask import Blueprint, jsonify, render_template, request, session, redirect, g

from app.session_id_generation import generate_secure_string
from .firebase_run import db, auth
from datetime import datetime

# Create a blueprint named 'auth'
login_bp = Blueprint('login', __name__, url_prefix='/')

@login_bp.route('/')
def index():
    # You can render templates and pass variables to them
    return render_template('login.html')

#after registering, magstore ng session data yung user sa session hehehe which we'll be using sa code
# yung session data is while they're logged in, pag naglogout sila, 
# mawawala yung session data nila sa session na iclear natin sa logout route hehe
# cache natin toh techniccalllyy??? HAHAHAHAHA IDDK MAN TS CRAZY
@login_bp.route('/login_user', methods=['POST'])
def login():
    token = request.json.get("token")

    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token["uid"]
        session["uid"] = uid
        session["email"] = decoded_token.get("email")
        session["name"] = decoded_token.get("name")
        session['picture'] = decoded_token.get("picture")
        session["current_session_id"] = generate_secure_string(20)
        print(decoded_token)
        return jsonify(success=True, uid=uid, name=decoded_token.get("name"))

    except Exception as e:
        return jsonify(success=False, error=str(e)), 401