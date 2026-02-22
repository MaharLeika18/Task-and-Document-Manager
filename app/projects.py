from flask import Blueprint, render_template
from datetime import datetime

from app import inject_session_data
from .decorators import auth_required

# Create a blueprint named 'projects'
projects_bp = Blueprint('projects', __name__, url_prefix='/')

@projects_bp.route('/', methods=['GET'])
@auth_required
def projects():
    return render_template("projects.html", user=inject_session_data())

@projects_bp.route('/create_project', methods=['GET'])
@auth_required  
def create_project():
    return render_template("create_project.html", user=inject_session_data())