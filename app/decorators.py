from functools import wraps
from flask import session, redirect, url_for

def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated via session
        if 'uid' not in session: 
            return redirect(url_for('login.index'))
        
        return f(*args, **kwargs)
        
    return decorated_function