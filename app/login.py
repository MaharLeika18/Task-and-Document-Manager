# hello_app/views.py
from flask import Blueprint, jsonify, render_template, request, session, redirect, g
from .firebase_run import db, auth
from datetime import datetime

# Create a blueprint named 'auth'
login_bp = Blueprint('login', __name__, url_prefix='/')

@login_bp.route('/')
def index():
    # You can render templates and pass variables to them
    return render_template('login.html')

@login_bp.route('/login_user', methods=['POST'])
def login():
    token = request.json.get("token")

    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token["uid"]

        # ✅ User verified
        return jsonify(success=True, uid=uid)

    except Exception as e:
        return jsonify(success=False, error=str(e)), 401