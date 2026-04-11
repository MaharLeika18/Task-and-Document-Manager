from flask import Blueprint, render_template, session
from datetime import datetime
from .decorators import auth_required
from .google_services import get_users, get_member_summaries

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
    member_summaries = get_member_summaries()

    for member in members:
        summary = member_summaries.get(member['uid'], {
            'projects_count': 0,
            'tasks_count': 0,
            'open_tasks_count': 0,
            'completed_tasks_count': 0
        })
        member.update(summary)

    return render_template("members.html", user=user, members=members)
