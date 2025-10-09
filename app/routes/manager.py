from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.models import db, User, Warehouse, Location
bp = Blueprint("manager", __name__, url_prefix="/manager")

@bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "Manager":
        return "Unauthorized", 403
    users = User.query.filter(User.role != "Manager").all()
    locations = Location.query.all()
    warehouses = Warehouse.query.all()
    return render_template(
        "manager_dashboard.html",
        users=users,
        locations=locations,
        warehouses=warehouses
    )

@bp.route("/add_user", methods=["POST"])
@login_required
def add_user():
    if current_user.role != "Manager":
        return "Unauthorized", 403
    username = request.form["username"]
    password = request.form["password"]
    role = request.form["role"]

    if User.query.filter_by(username=username).first():
        flash("Username already exists!", "error")
        return redirect(url_for("manager.dashboard"))

    new_user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role=role,
        is_active=True
    )
    db.session.add(new_user)
    db.session.commit()
    flash(f"New {role} '{username}' added successfully!", "success")
    return redirect(url_for("manager.dashboard"))

@bp.route("/toggle_user/<int:user_id>")
@login_required
def toggle_user(user_id):
    if current_user.role != "Manager":
        return "Unauthorized", 403
    user = User.query.get(user_id)
    if user:
        user.is_active = not user.is_active
        db.session.commit()
        state = "enabled" if user.is_active else "disabled"
        flash(f"User '{user.username}' {state}.", "success")
    else:
        flash("User not found.", "error")
    return redirect(url_for("manager.dashboard"))

@bp.route("/update_password/<int:user_id>", methods=["POST"])
@login_required
def update_password(user_id):
    if current_user.role != "Manager":
        return "Unauthorized", 403
    new_password = request.form["new_password"]
    user = User.query.get(user_id)
    if user:
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash(f"Password updated for '{user.username}'.", "success")
    else:
        flash("User not found.", "error")
    return redirect(url_for("manager.dashboard"))


@bp.route("/")
@login_required
def insights():
    if current_user.role != "Manager":
        return "Unauthorized", 403
    return render_template("manager_insights.html", current_user=current_user)


@bp.route("/add_location", methods=["POST"])
def add_location():
    name = request.form["name"]
    loc = Location(name=name, created_by=current_user.username)
    db.session.add(loc)
    db.session.commit()
    flash("Location added successfully", "success")
    return redirect(url_for("manager.dashboard"))

@bp.route("/add_warehouse", methods=["POST"])
def add_warehouse():
    name = request.form["warehouse_name"]
    location_id = request.form["location_id"]
    wh = Warehouse(warehouse_name=name, location_id=location_id, created_by=current_user.username)
    db.session.add(wh)
    db.session.commit()
    flash("Warehouse added successfully", "success")
    return redirect(url_for("manager.dashboard"))

@bp.route("/delete_location/<int:location_id>")
def delete_location(location_id):
    loc = Location.query.get(location_id)
    db.session.delete(loc)
    db.session.commit()
    flash("Location deleted", "success")
    return redirect(url_for("manager.dashboard"))

@bp.route("/delete_warehouse/<int:warehouse_id>")
def delete_warehouse(warehouse_id):
    wh = Warehouse.query.get(warehouse_id)
    if wh and len(wh.scan_lines) > 0:
        flash("Cannot delete warehouse — lines exist.", "danger")
        return redirect(url_for("manager.dashboard"))
    db.session.delete(wh)
    db.session.commit()
    flash("Warehouse deleted successfully", "success")
    return redirect(url_for("manager.dashboard"))