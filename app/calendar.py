from flask import Blueprint, render_template
from datetime import datetime

# Create a blueprint named 'calendar'
calendar_bp = Blueprint('calendar', __name__, url_prefix='/')

@calendar_bp.route('/calendar', methods=['GET'])
def calendar(): 
    return "Calendar Page - Under Construction"