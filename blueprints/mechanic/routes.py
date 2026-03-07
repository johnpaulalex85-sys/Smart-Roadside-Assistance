from flask import render_template, redirect, url_for, session, flash, request
from blueprints.mechanic import mechanic_bp
from extensions import mongo
from bson import ObjectId
from utils.notifications import send_sms_alert



def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "mechanic":
            flash("Please login as a mechanic.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ─── Dashboard ────────────────────────────────────────────────────────────────
@mechanic_bp.route("/dashboard")
@login_required
def dashboard():
    mechanic_id = ObjectId(session["mechanic_id"])
    mechanic = mongo.db.mechanics.find_one({"_id": mechanic_id})

    assigned_requests = list(
        mongo.db.service_requests.find(
            {"assigned_mechanic_id": mechanic_id, "status": {"$in": ["Assigned", "In Process"]}}
        ).sort("created_at", -1)
    )
    completed_requests = list(
        mongo.db.service_requests.find(
            {"assigned_mechanic_id": mechanic_id, "status": "Completed"}
        ).sort("created_at", -1)
    )

    for req in assigned_requests + completed_requests:
        if req.get("user_id"):
            req["user"] = mongo.db.users.find_one({"_id": req["user_id"]})

    return render_template(
        "mechanic/dashboard.html",
        mechanic=mechanic,
        assigned_requests=assigned_requests,
        completed_requests=completed_requests,
    )


# ─── Update Status ────────────────────────────────────────────────────────────
@mechanic_bp.route("/update_status/<request_id>", methods=["POST"])
@login_required
def update_status(request_id):
    new_status = request.form.get("status")
    allowed = {"In Process", "Completed"}
    if new_status not in allowed:
        flash("Invalid status.", "danger")
        return redirect(url_for("mechanic.dashboard"))

    mongo.db.service_requests.update_one(
        {
            "_id": ObjectId(request_id),
            "assigned_mechanic_id": ObjectId(session["mechanic_id"]),
        },
        {"$set": {"status": new_status}},
    )
    
    if new_status == "Completed":
        req = mongo.db.service_requests.find_one({"_id": ObjectId(request_id)})
        if req and req.get("user_id"):
            user = mongo.db.users.find_one({"_id": req["user_id"]})
            if user and user.get("phone"):
                from utils.notifications import send_sms_alert
                send_sms_alert(user["phone"], "Your Road Rescue request has been marked as COMPLETED by the mechanic. Please proceed to payment.")
                
    flash(f"Request marked as '{new_status}'.", "success")
    return redirect(url_for("mechanic.dashboard"))
