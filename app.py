import os
from flask import Flask, url_for, Blueprint, render_template, request, session, redirect

from app import create_app

app = create_app()
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")

if __name__ == "__main__":
    app.run(debug=True)