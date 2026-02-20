from flask import Blueprint, render_template
from datetime import datetime

from app import session_data
from .decorators import auth_required

# Create a blueprint named 'calendar'
calendar_bp = Blueprint('calendar', __name__, url_prefix='/')

@calendar_bp.route('/calendar', methods=['GET'])
@auth_required
def calendar(): 
    user_data = session_data()
    
    return render_template("calendar.html", user_data=user_data)