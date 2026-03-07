from flask import render_template, redirect, url_for, session, flash, request
from blueprints.admin import admin_bp
from extensions import mongo
from werkzeug.security import generate_password_hash
from bson import ObjectId



def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Please login as an admin.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def _seed_admin():
    """Insert a default admin if none exists."""
    if not mongo.db.admins.find_one({"email": "admin@roadrescue.com"}):
        mongo.db.admins.insert_one({
            "email": "admin@roadrescue.com",
            "password": generate_password_hash("Admin@1234"),
            "name": "Super Admin",
            "role": "admin",
        })


# ─── Dashboard ────────────────────────────────────────────────────────────────
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    _seed_admin()
    stats = {
        "total_users": mongo.db.users.count_documents({}),
        "total_workshops": mongo.db.workshops.count_documents({}),
        "total_mechanics": mongo.db.mechanics.count_documents({}),
        "total_requests": mongo.db.service_requests.count_documents({}),
        "pending": mongo.db.service_requests.count_documents({"status": "Pending"}),
        "in_process": mongo.db.service_requests.count_documents({"status": {"$in": ["Accepted", "Assigned", "In Process"]}}),
        "completed": mongo.db.service_requests.count_documents({"status": "Completed"}),
        "revenue": sum([r.get("estimated_cost", 0) for r in mongo.db.service_requests.find({"payment_status": "Completed"})]),
    }
    recent_requests = list(
        mongo.db.service_requests.find().sort("created_at", -1).limit(5)
    )
    for req in recent_requests:
        req["user"] = mongo.db.users.find_one({"_id": req.get("user_id")})
    return render_template("admin/dashboard.html", stats=stats, recent_requests=recent_requests)


# ─── Manage Users ─────────────────────────────────────────────────────────────
@admin_bp.route("/users")
@login_required
def manage_users():
    users = list(mongo.db.users.find().sort("created_at", -1))
    return render_template("admin/manage_users.html", users=users)

@admin_bp.route("/users/<user_id>/toggle_block", methods=["POST"])
@login_required
def toggle_user_block(user_id):
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        new_status = not user.get("is_blocked", False)
        mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"is_blocked": new_status}})
        flash(f"User {'blocked' if new_status else 'unblocked'} successfully.", "success")
    return redirect(url_for("admin.manage_users"))


# ─── Manage Workshops ─────────────────────────────────────────────────────────
@admin_bp.route("/workshops")
@login_required
def manage_workshops():
    workshops = list(mongo.db.workshops.find())
    for w in workshops:
        w["mechanic_count"] = mongo.db.mechanics.count_documents({"workshop_id": w["_id"]})
    return render_template("admin/manage_workshops.html", workshops=workshops)

@admin_bp.route("/workshops/<workshop_id>/status", methods=["POST"])
@login_required
def update_workshop_status(workshop_id):
    action = request.form.get("action")
    if action in ["approve", "reject"]:
        new_status = "approved" if action == "approve" else "rejected"
        mongo.db.workshops.update_one(
            {"_id": ObjectId(workshop_id)},
            {"$set": {"status": new_status}}
        )
        flash(f"Workshop {new_status} successfully.", "success")
    return redirect(url_for("admin.manage_workshops"))

@admin_bp.route("/workshops/<workshop_id>/toggle_block", methods=["POST"])
@login_required
def toggle_workshop_block(workshop_id):
    workshop = mongo.db.workshops.find_one({"_id": ObjectId(workshop_id)})
    if workshop:
        new_status = not workshop.get("is_blocked", False)
        mongo.db.workshops.update_one({"_id": ObjectId(workshop_id)}, {"$set": {"is_blocked": new_status}})
        flash(f"Workshop {'blocked' if new_status else 'unblocked'} successfully.", "success")
    return redirect(url_for("admin.manage_workshops"))


# ─── Manage Requests ──────────────────────────────────────────────────────────
@admin_bp.route("/requests")
@login_required
def manage_requests():
    requests_list = list(mongo.db.service_requests.find().sort("created_at", -1))
    for req in requests_list:
        req["user"] = mongo.db.users.find_one({"_id": req.get("user_id")})
        req["workshop"] = mongo.db.workshops.find_one({"_id": req.get("workshop_id")}) if req.get("workshop_id") else None
        req["mechanic"] = mongo.db.mechanics.find_one({"_id": req.get("assigned_mechanic_id")}) if req.get("assigned_mechanic_id") else None
    return render_template("admin/manage_requests.html", requests=requests_list)
