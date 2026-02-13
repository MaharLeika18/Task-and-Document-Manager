# hello_app/views.py
from flask import Blueprint, render_template
from datetime import datetime

# Create a blueprint named 'auth'
auth_bp = Blueprint('auth', __name__, url_prefix='/')

@auth_bp.route('/login')
def index():
    # You can render templates and pass variables to them
    return render_template('login.html')
#firebase code here
