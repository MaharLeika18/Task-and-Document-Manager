# hello_app/__init__.py
import os
from flask import Flask, url_for, Blueprint, render_template, request, session, redirect
app = Flask(__name__)

# Import the blueprint from views.py and register it

def create_app():
    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    return app

@app.route('/', methods=['GET', 'POST'])
def home():
    pass