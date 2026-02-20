from functools import wraps
from flask import session, redirect, url_for

# this makes sure to check if nakalogin yung user hehe 
# if not, ireredirect sila sa login page   
def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated via session
        if 'uid' not in session: 
            return redirect(url_for('login.index'))
        
        return f(*args, **kwargs)
        
    return decorated_function