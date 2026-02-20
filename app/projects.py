from flask import Blueprint, render_template
from datetime import datetime

from app import session_data
from .decorators import auth_required

# Create a blueprint named 'projects'
projects_bp = Blueprint('projects', __name__, url_prefix='/')

@projects_bp.route('/', methods=['GET'])
@auth_required
def projects():
    user_data = session_data()
    
    return render_template("projects.html", user=user_data)