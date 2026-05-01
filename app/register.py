# hello_app/views.py
from flask import Blueprint, jsonify, render_template, request, session, redirect, g
from .firebase_run import db, auth, verify_id_token_with_retry
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
    user_data = request.json.get("user_data")
    try:
        decoded = verify_id_token_with_retry(token)
        session["uid"] = decoded["uid"]
        session["email"] = decoded.get("email")
        session["name"] = (
            decoded.get("name") or 
            user_data.get("display_name") or 
            "User"
        )
        session["picture"] = (
            decoded.get("picture") or 
            "/static/default-avatar.png"
        )        
        session["current_session_id"] = generate_secure_string(20)
        
        # Save user data to Firestore
        if user_data:
            user_ref = db.collection('users').document(decoded["uid"])
            user_ref.set({
                'uid': decoded["uid"],
                'username': user_data.get('username', ''),
                'display_name': user_data.get('display_name', ''),
                'email': decoded.get("email"),
                'date_created': user_data.get('date_created', ''),
                'picture': decoded.get("picture") or "/static/default-avatar.png",
                'google_picture': decoded.get("picture", ""),
                'photo_source': 'google' if decoded.get("firebase", {}).get("sign_in_provider") == "google.com" else 'email'
            })
        
        return jsonify(success=True)

    except Exception as e:
        return jsonify(success=False, error=str(e)), 401

