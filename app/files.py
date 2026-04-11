from flask import Blueprint, render_template, session
from datetime import datetime
from .decorators import auth_required

# Create a blueprint named 'files'
files_bp = Blueprint('files', __name__, url_prefix='/')

@files_bp.route('/files', methods=['GET'])
@auth_required
def files():
    user = {
        "uid": session["uid"],
        "email": session["email"],
        "name": session["name"],
        "picture": session["picture"],
        "current_session_id": session["current_session_id"]
    }
    return render_template("files.html", user=user)