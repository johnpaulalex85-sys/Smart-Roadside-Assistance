from flask import render_template, request, redirect, url_for, session, flash, jsonify
from blueprints.workshop import workshop_bp
from extensions import mongo
from bson import ObjectId
from werkzeug.security import generate_password_hash
from utils.notifications import send_sms_alert



def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "workshop":
            flash("Please login as a workshop.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ─── Dashboard ────────────────────────────────────────────────────────────────
@workshop_bp.route("/dashboard")
@login_required
def dashboard():
    workshop_id = ObjectId(session["workshop_id"])
    workshop = mongo.db.workshops.find_one({"_id": workshop_id})

    pending_requests = list(
        mongo.db.service_requests.find({
            "status": "Pending",
            "$or": [{"workshop_id": None}, {"workshop_id": workshop_id}]
        }).sort("created_at", -1)
    )
    accepted_requests = list(
        mongo.db.service_requests.find(
            {"workshop_id": workshop_id, "status": {"$in": ["Accepted", "Assigned", "In Process", "Completed"]}}
        ).sort("created_at", -1)
    )

    # Attach user info and mechanic info
    for req in pending_requests + accepted_requests:
        if req.get("user_id"):
            req["user"] = mongo.db.users.find_one({"_id": req["user_id"]})
        if req.get("assigned_mechanic_id"):
            req["mechanic"] = mongo.db.mechanics.find_one({"_id": req["assigned_mechanic_id"]})

    mechanics = list(mongo.db.mechanics.find({"workshop_id": workshop_id}))
    available_mechanics = [m for m in mechanics if m.get("status") == "available"]

    stats = {
        "total_mechanics": len(mechanics),
        "pending": len(pending_requests),
        "active": len([r for r in accepted_requests if r["status"] in ("Accepted", "Assigned", "In Process")]),
        "completed": len([r for r in accepted_requests if r["status"] == "Completed"]),
    }

    return render_template(
        "workshop/dashboard.html",
        workshop=workshop,
        pending_requests=pending_requests,
        accepted_requests=accepted_requests,
        mechanics=mechanics,
        available_mechanics=available_mechanics,
        stats=stats,
    )


# ─── Accept Request ───────────────────────────────────────────────────────────
@workshop_bp.route("/accept/<request_id>", methods=["POST"])
@login_required
def accept_request(request_id):
    estimated_cost = request.form.get("estimated_cost", "0")
    try:
        cost = float(estimated_cost)
    except ValueError:
        cost = 0.0

    mongo.db.service_requests.update_one(
        {"_id": ObjectId(request_id), "status": "Pending"},
        {"$set": {
            "workshop_id": ObjectId(session["workshop_id"]),
            "status": "Accepted",
            "estimated_cost": cost
        }},
    )
    
    req = mongo.db.service_requests.find_one({"_id": ObjectId(request_id)})
    if req and req.get("user_id"):
        user = mongo.db.users.find_one({"_id": req["user_id"]})
        if user and user.get("phone"):
            send_sms_alert(user["phone"], f"Your request has been ACCEPTED by a workshop. Estimated Cost: ${cost:.2f}")

    flash("Request accepted!", "success")
    return redirect(url_for("workshop.dashboard"))


# ─── Assign Mechanic ──────────────────────────────────────────────────────────
@workshop_bp.route("/assign/<request_id>", methods=["POST"])
@login_required
def assign_mechanic(request_id):
    mechanic_id = request.form.get("mechanic_id")
    if not mechanic_id:
        flash("Please select a mechanic.", "warning")
        return redirect(url_for("workshop.dashboard"))

    mongo.db.service_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"assigned_mechanic_id": ObjectId(mechanic_id), "status": "Assigned"}},
    )
    
    req = mongo.db.service_requests.find_one({"_id": ObjectId(request_id)})
    if req and req.get("user_id"):
        user = mongo.db.users.find_one({"_id": req["user_id"]})
        if user and user.get("phone"):
            send_sms_alert(user["phone"], "A mechanic has been ASSIGNED to your request and is reviewing it.")
            
    flash("Mechanic assigned successfully!", "success")
    return redirect(url_for("workshop.dashboard"))


# ─── Add Mechanic ─────────────────────────────────────────────────────────────
@workshop_bp.route("/add_mechanic", methods=["POST"])
@login_required
def add_mechanic():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if mongo.db.mechanics.find_one({"email": email}):
        flash("Mechanic email already exists.", "warning")
        return redirect(url_for("workshop.dashboard"))

    mongo.db.mechanics.insert_one({
        "name": name,
        "email": email,
        "password": generate_password_hash(password),
        "workshop_id": ObjectId(session["workshop_id"]),
        "status": "available",
        "role": "mechanic",
    })
    flash(f"Mechanic '{name}' added successfully!", "success")
    return redirect(url_for("workshop.dashboard"))


# ─── Delete Mechanic ──────────────────────────────────────────────────────────
@workshop_bp.route("/delete_mechanic/<mechanic_id>", methods=["POST"])
@login_required
def delete_mechanic(mechanic_id):
    mechanic = mongo.db.mechanics.find_one({"_id": ObjectId(mechanic_id), "workshop_id": ObjectId(session["workshop_id"])})
    if not mechanic:
        flash("Mechanic not found.", "danger")
        return redirect(url_for("workshop.dashboard"))

    # Optional: We could check if they have active jobs, but for simplicity we allow deletion.
    # Alternatively we just delete them. If they have active jobs, the workshop might need to reassign.
    mongo.db.mechanics.delete_one({"_id": ObjectId(mechanic_id)})
    
    # Reset any active requests assigned to this mechanic back to workshop pool
    mongo.db.service_requests.update_many(
        {"assigned_mechanic_id": ObjectId(mechanic_id), "status": "Assigned"},
        {"$set": {"assigned_mechanic_id": None, "status": "Accepted"}}
    )

    flash(f"Mechanic '{mechanic['name']}' deleted successfully.", "success")
    return redirect(url_for("workshop.dashboard"))


# ─── Available Mechanics JSON ─────────────────────────────────────────────────
@workshop_bp.route("/mechanics_json")
@login_required
def mechanics_json():
    mechanics = list(
        mongo.db.mechanics.find(
            {"workshop_id": ObjectId(session["workshop_id"]), "status": "available"},
            {"name": 1}
        )
    )
    return jsonify([{"id": str(m["_id"]), "name": m["name"]} for m in mechanics])
