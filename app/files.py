from flask import Blueprint, render_template
from datetime import datetime

# Create a blueprint named 'files'
files_bp = Blueprint('files', __name__, url_prefix='/')

@files_bp.route('/files', methods=['GET'])
def files():
    return "Files Page - Under Construction"