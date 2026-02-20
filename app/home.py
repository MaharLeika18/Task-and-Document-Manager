from flask import Blueprint, render_template, session, redirect
from datetime import datetime
from flask_login import login_required

from app import session_data

from .decorators import auth_required
from app.session_id_generation import generate_secure_string
from .firebase_run import verify_firebase_token

# Create a blueprint named 'home'
home_bp = Blueprint('home', __name__, url_prefix='/')

@home_bp.route('/', methods=['GET'])
@auth_required
def home():
    user_data = session_data()

    return render_template("home.html", user=user_data)