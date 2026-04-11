from flask import Blueprint, render_template, jsonify, session
from datetime import datetime

from app import inject_session_data
from .decorators import auth_required
from .google_services import get_user_calendar_events

# Create a blueprint named 'calendar'
calendar_bp = Blueprint('calendar', __name__, url_prefix='/')

@calendar_bp.route('/calendar', methods=['GET'])
@auth_required
def calendar(): 
    return render_template("calendar.html", user=inject_session_data())

@calendar_bp.route('/calendar/events', methods=['GET'])
@auth_required
def calendar_events():
    user_uid = session['uid']
    events = get_user_calendar_events(user_uid)
    return jsonify({'success': True, 'events': events})