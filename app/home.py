from flask import Blueprint, render_template, session, redirect
from datetime import datetime
from flask_login import login_required

from app.session_id_generation import generate_secure_string
from .firebase_run import verify_firebase_token

# Create a blueprint named 'home'
home_bp = Blueprint('home', __name__, url_prefix='/')

@home_bp.route('/', methods=['GET'])
def home():
    if "uid" not in session:
        return redirect("/login")

    uid = session["uid"]
    email = session["email"]
    session["current_session_id"] = generate_secure_string(20)
    user_data = {
        "uid": uid,
        "email": email
    }

    return render_template("home.html", user=user_data)