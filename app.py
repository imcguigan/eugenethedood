from flask import Flask, request, redirect, url_for, session, flash, render_template
from functools import wraps

# Check to see if user is logged into admin site. If not redirects them to gallery
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__) #runs the app
app.secret_key = '' #this is used for the cookie

@app.route('/')
def gallery():
    return render_template('gallery.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    # Hardcoded credentials (just for this example)
    admin_username = ""
    admin_password = ""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == admin_username and password == admin_password:
            session['logged_in'] = True
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('admin-login.html')

@app.route('/admin-dashboard')
@login_required # This protects the route for only logged in users
def admin_dashboard():
    return render_template('admin-dashboard.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('gallery'))








