from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from ..models import db, User

bp = Blueprint("auth", __name__)


@bp.route("/")
def index():
    # Redirect to login if not logged in
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))

    # Redirect to role-based dashboard if already logged in
    role = current_user.role
    if role == "Manager":
        return redirect(url_for("manager.insights"))
    elif role == "TeamLeader":
        return redirect(url_for("team_leader.dashboard"))
    elif role == "Counter":
        return redirect(url_for("counter.dashboard"))
    return redirect(url_for("auth.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password) and user.is_active:
            login_user(user)
            flash(f"Welcome, {user.role}!", "success")
            if user.role == "Manager":
                return redirect(url_for("manager.insights"))
            elif user.role == "TeamLeader":
                return redirect(url_for("team_leader.dashboard"))
            elif user.role == "Counter":
                return redirect(url_for("counter.dashboard"))
        else:
            flash("Invalid credentials or inactive user", "danger")

    return render_template("login.html")

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))