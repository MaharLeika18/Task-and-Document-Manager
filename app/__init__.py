# hello_app/__init__.py
import os
from flask import Flask, url_for,jsonify, g, Blueprint, render_template, request, session, redirect
from .firebase_run import verify_firebase_token
from functools import wraps
# In your __init__.py
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# Import the blueprint from views.py and register it

def create_app():
    from .login import login_bp
    from .home import home_bp
    from .files import files_bp
    from .members import members_bp
    from .calendar import calendar_bp
    from .register import register_bp
    from .projects import projects_bp
    from .firebase_run import db, auth, verify_firebase_token
    app.register_blueprint(home_bp, url_prefix='/home')
    app.register_blueprint(files_bp, url_prefix='/files')
    app.register_blueprint(members_bp, url_prefix='/members')
    app.register_blueprint(login_bp, url_prefix='/login')
    app.register_blueprint(register_bp, url_prefix='/register')
    app.register_blueprint(calendar_bp, url_prefix='/calendar')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    
    return app


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login.index'))

# yung nakuhang session data sa register.py or login.py 
# dito ko na lang nilagay sa isang func where will turn it into a dict man HAAHAHAHA
def session_data():
    if "uid" not in session:
        return redirect("/login")
    
    return {
        "uid": session["uid"],
        "email": session["email"],
        "name": session["name"],
        "picture": session["picture"],
        "current_session_id": session["current_session_id"]
    }
