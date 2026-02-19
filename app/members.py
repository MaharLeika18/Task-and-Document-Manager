from flask import Blueprint, render_template
from datetime import datetime

# Create a blueprint named 'members'
members_bp = Blueprint('members', __name__, url_prefix='/')

@members_bp.route('/members', methods=['GET'])
def members():
    return "Members Page - Under Construction"
