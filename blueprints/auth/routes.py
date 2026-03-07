import os
import re
from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from blueprints.auth import auth_bp
from extensions import mongo
from datetime import datetime, timedelta
from utils.notifications import send_email_notification


def is_valid_password(pwd: str) -> bool:
    if not isinstance(pwd, str): return False
    return len(pwd) >= 8 and bool(re.search(r"[A-Z]", pwd)) and bool(re.search(r"\d", pwd))


def _allowed_role_login(collection, email, password, role_key, id_key):
    record = mongo.db[collection].find_one({"email": email})
    if not record:
        return None

    # Check if account is locked
    if record.get("locked_until") and record["locked_until"] > datetime.utcnow():
        return "LOCKED"

    # Check if workshop is pending approval
    if role_key == "workshop" and record.get("status") == "pending":
        return "PENDING_APPROVAL"
        
    # Check if account is blocked by admin
    if record.get("is_blocked"):
        return "BLOCKED"

    if check_password_hash(record["password"], password):
        # Reset failed attempts on success
        if record.get("failed_attempts", 0) > 0:
            mongo.db[collection].update_one(
                {"_id": record["_id"]},
                {"$set": {"failed_attempts": 0, "locked_until": None}}
            )

        session.clear()
        session[id_key] = str(record["_id"])
        session["role"] = role_key
        session["name"] = record.get("name", record.get("email", ""))
        return record
    else:
        # Increment failed attempts on failure
        attempts = record.get("failed_attempts", 0) + 1
        updates = {"failed_attempts": attempts}
        if attempts >= 5:
            updates["locked_until"] = datetime.utcnow() + timedelta(minutes=15)
        
        mongo.db[collection].update_one({"_id": record["_id"]}, {"$set": updates})
        return "INVALID"


# ─── Login ───────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        collection_map = {
            "user": ("users", "user_id", "user.dashboard"),
            "workshop": ("workshops", "workshop_id", "workshop.dashboard"),
            "mechanic": ("mechanics", "mechanic_id", "mechanic.dashboard"),
            "admin": ("admins", "admin_id", "admin.dashboard")
        }

        if role in collection_map:
            coll, id_key, endpoint = collection_map[role]
            rec = _allowed_role_login(coll, email, password, role, id_key)
            
            if isinstance(rec, dict):
                return redirect(url_for(endpoint))
            elif rec == "LOCKED":
                flash("Account locked due to too many failed attempts. Try again in 15 minutes.", "danger")
                return render_template("auth/login.html")
            elif rec == "PENDING_APPROVAL":
                flash("Your workshop account is pending admin approval. Please check back later.", "warning")
                return render_template("auth/login.html")
            elif rec == "BLOCKED":
                flash("Your account has been suspended by an administrator. Please contact support.", "danger")
                return render_template("auth/login.html")

        flash("Invalid email or password. Please try again.", "danger")
    return render_template("auth/login.html")


# ─── Register User ────────────────────────────────────────────────────────────
@auth_bp.route("/register/user", methods=["GET", "POST"])
def register_user():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        if not is_valid_password(password):
            flash("Password must be at least 8 characters long, contain an uppercase letter and a number.", "warning")
            return redirect(url_for("auth.register_user"))

        if mongo.db.users.find_one({"email": email}):
            flash("Email already registered.", "warning")
            return redirect(url_for("auth.register_user"))

        mongo.db.users.insert_one({
            "name": name,
            "email": email,
            "password": generate_password_hash(password),
            "phone": phone,
            "role": "user",
            "failed_attempts": 0,
            "locked_until": None,
            "created_at": datetime.utcnow(),
        })
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register_user.html")


# ─── Register Workshop ────────────────────────────────────────────────────────
@auth_bp.route("/register/workshop", methods=["GET", "POST"])
def register_workshop():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        location_name = request.form.get("location_name", "").strip()
        
        lat_str = request.form.get("latitude", "0").strip()
        lng_str = request.form.get("longitude", "0").strip()
        try:
            latitude = float(lat_str) if lat_str else 0.0
            longitude = float(lng_str) if lng_str else 0.0
        except ValueError:
            latitude = 0.0
            longitude = 0.0

        if not is_valid_password(password):
            flash("Password must be at least 8 characters long, contain an uppercase letter and a number.", "warning")
            return redirect(url_for("auth.register_workshop"))

        if mongo.db.workshops.find_one({"email": email}):
            flash("Email already registered.", "warning")
            return redirect(url_for("auth.register_workshop"))

        mongo.db.workshops.insert_one({
            "name": name,
            "email": email,
            "password": generate_password_hash(password),
            "phone": phone,
            "location_name": location_name,
            "location": {
                "type": "Point",
                "coordinates": [longitude, latitude],
            },
            "role": "workshop",
            "failed_attempts": 0,
            "locked_until": None,
            "status": "pending", # New: Phase 3 Approval requirement
            "created_at": datetime.utcnow()
        })
        
        send_email_notification(email, "Workshop Registration Received", f"Hi {name}, your workshop application is under admin review.")
        
        flash("Workshop registered and pending admin approval! Please login once approved.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register_workshop.html")


# ─── Logout ───────────────────────────────────────────────────────────────────
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

