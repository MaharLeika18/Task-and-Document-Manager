# hello_app/__init__.py
import os
from flask import Flask, url_for, Blueprint, render_template, request, session, redirect
app = Flask(__name__)

# Import the blueprint from views.py and register it

def create_app():
    from .accounts import accounts_bp
    from .home import home_bp
    from .files import files_bp
    from .members import members_bp
    from .calendar import calendar_bp
    from .projects import projects_bp
    from .firebase_run import db, auth
    app.register_blueprint(home_bp, url_prefix='/home')
    app.register_blueprint(files_bp, url_prefix='/files')
    app.register_blueprint(members_bp, url_prefix='/members')
    app.register_blueprint(accounts_bp, url_prefix='/accounts')
    app.register_blueprint(calendar_bp, url_prefix='/calendar')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    
    return app

@app.route('/', methods=['GET', 'POST'])
def index():
    pass