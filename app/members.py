from flask import Blueprint, render_template, session
from datetime import datetime
from .decorators import auth_required
from .google_services import get_users

# Create a blueprint named 'members'
members_bp = Blueprint('members', __name__, url_prefix='/')

@members_bp.route('/members', methods=['GET'])
@auth_required
def members():
    user = {
        "uid": session["uid"],
        "email": session["email"],
        "name": session["name"],
        "picture": session["picture"],
        "current_session_id": session["current_session_id"]
    }
    members = get_users()
    return render_template("members.html", user=user, members=members)
