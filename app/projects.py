from flask import Blueprint, render_template
from datetime import datetime

# Create a blueprint named 'projects'
projects_bp = Blueprint('projects', __name__, url_prefix='/')

@projects_bp.route('/projects', methods=['GET'])
def projects():
    return "Projects Page - Under Construction"