# hello_app/views.py
from flask import Blueprint, render_template
from .firebase_run import db, auth
from datetime import datetime

# Create a blueprint named 'auth'
accounts_bp = Blueprint('accounts', __name__, url_prefix='/')

@accounts_bp.route('/')
def index():
    # You can render templates and pass variables to them
    return render_template('login.html')
#firebase code here
