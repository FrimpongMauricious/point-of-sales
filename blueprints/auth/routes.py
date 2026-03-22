from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from functools import wraps

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                return render_template('errors/403.html'), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route('/login', methods=['GET', 'POST'])
@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.is_active:
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            return _redirect_by_role(user.role)
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


def _redirect_by_role(role):
    if role == 'admin':
        return redirect(url_for('dashboard.admin'))
    elif role == 'manager':
        return redirect(url_for('dashboard.manager'))
    else:
        return redirect(url_for('sales.pos'))


# Make login accessible at /login directly
from flask import Blueprint as _Blueprint
_login_bp = Blueprint('login_redirect', __name__)

@_login_bp.route('/login')
def login_redirect():
    return redirect(url_for('auth.login'))
