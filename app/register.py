# hello_app/views.py
from flask import Blueprint, jsonify, render_template, request, session, redirect, g
from .firebase_run import db, auth
from datetime import datetime
from .session_id_generation import generate_secure_string
# Create a blueprint named 'auth'
register_bp = Blueprint('register', __name__, url_prefix='/')

@register_bp.route('/')
def index():
    # You can render templates and pass variables to them
    return render_template('login.html')

#after registering, magstore ng session data yung user sa session hehehe which we'll be using sa code
# yung session data is while they're logged in, pag naglogout sila, 
# mawawala yung session data nila sa session na iclear natin sa logout route hehe
# cache natin toh techniccalllyy??? HAHAHAHAHA IDDK MAN TS CRAZY
@register_bp.route("/register_user", methods=["POST"])
def register():
    token = request.json.get("token")
    try:
        decoded = auth.verify_id_token(token)
        session["uid"] = decoded["uid"]
        session["email"] = decoded.get("email")
        session["name"] = decoded.get("name")
        session['picture'] = decoded.get("picture")
        session["current_session_id"] = generate_secure_string(20)
        

        return jsonify(success=True)

    except Exception as e:
        return jsonify(success=False, error=str(e)), 401

