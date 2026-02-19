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

@register_bp.route("/register_user", methods=["POST"])
def register():
    token = request.json.get("token")
    try:
        decoded = auth.verify_id_token(token)

        session["uid"] = decoded["uid"]
        session["email"] = decoded.get("email")
        

        return jsonify(success=True)

    except Exception as e:
        return jsonify(success=False, error=str(e)), 401

