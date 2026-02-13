from flask import Blueprint, render_template
from datetime import datetime

# Create a blueprint named 'files'
files_bp = Blueprint('files', __name__, url_prefix='/')