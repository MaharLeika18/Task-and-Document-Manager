from flask import Blueprint, render_template
from datetime import datetime

# Create a blueprint named 'projects'
projects_bp = Blueprint('projects', __name__, url_prefix='/')