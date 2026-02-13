from flask import Blueprint, render_template
from datetime import datetime

# Create a blueprint named 'home'
home_bp = Blueprint('home', __name__, url_prefix='/')