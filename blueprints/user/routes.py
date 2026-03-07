import os
from flask import render_template, request, redirect, url_for, session, flash, current_app, jsonify
from werkzeug.utils import secure_filename
from blueprints.user import user_bp
from extensions import mongo
from bson import ObjectId
from utils.notifications import send_sms_alert
from datetime import datetime, timedelta




def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "user":
            flash("Please login as a user.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename):
    allowed = current_app.config["ALLOWED_EXTENSIONS"]
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


# ─── Dashboard ────────────────────────────────────────────────────────────────
@user_bp.route("/dashboard")
@login_required
def dashboard():
    user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})
    requests_list = list(
        mongo.db.service_requests.find({"user_id": ObjectId(session["user_id"])}).sort("created_at", -1)
    )
    # Attach mechanic info
    for req in requests_list:
        if req.get("assigned_mechanic_id"):
            req["mechanic"] = mongo.db.mechanics.find_one({"_id": req["assigned_mechanic_id"]})
        if req.get("workshop_id"):
            req["workshop"] = mongo.db.workshops.find_one({"_id": req["workshop_id"]})
    return render_template("user/dashboard.html", user=user, requests=requests_list)


# ─── Request Service ──────────────────────────────────────────────────────────
@user_bp.route("/request", methods=["GET", "POST"])
@login_required
def request_service():
    if request.method == "POST":
        vehicle_type = request.form.get("vehicle_type", "")
        vehicle_company = request.form.get("vehicle_company", "")
        vehicle_model = request.form.get("vehicle_model", "")
        vehicle_year = request.form.get("vehicle_year", "")
        description = request.form.get("description", "")
        
        location_name = request.form.get("location_name", "").strip()
        lat_str = request.form.get("latitude", "0").strip()
        lng_str = request.form.get("longitude", "0").strip()
        try:
            latitude = float(lat_str) if lat_str else 0.0
            longitude = float(lng_str) if lng_str else 0.0
        except ValueError:
            latitude = 0.0
            longitude = 0.0

        media = []
        files = request.files.getlist("media")
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        for f in files:
            if f and f.filename and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                # Make unique
                unique_name = f"{int(datetime.utcnow().timestamp())}_{filename}"
                save_path = os.path.join(upload_folder, unique_name)
                f.save(save_path)
                media.append(f"uploads/{unique_name}")

        insert_result = mongo.db.service_requests.insert_one({
            "user_id": ObjectId(session["user_id"]),
            "workshop_id": None,
            "assigned_mechanic_id": None,
            "vehicle_type": vehicle_type,
            "vehicle_company": vehicle_company,
            "vehicle_model": vehicle_model,
            "vehicle_year": vehicle_year,
            "description": description,
            "location_name": location_name,
            "location_coords": [longitude, latitude],
            "media": media,
            "status": "Pending",
            "payment_status": "Pending",
            "payment_id": None,
            "estimated_cost": None,
            "created_at": datetime.utcnow(),
        })
        
        # If directed to a specific workshop, update the query
        workshop_id_param = request.form.get("workshop_id")
        if workshop_id_param:
            mongo.db.service_requests.update_one(
                {"_id": insert_result.inserted_id},
                {"$set": {"workshop_id": ObjectId(workshop_id_param)}}
            )
        
        user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})
        if user and user.get("phone"):
            send_sms_alert(user["phone"], f"Your Smart Roadside Assistance request for {vehicle_company} {vehicle_model} has been submitted and is pending workshop acceptance.")
            
        flash("Service request submitted successfully!", "success")
        return redirect(url_for("user.dashboard"))

    user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})
    
    selected_workshop = None
    target_workshop_id = request.args.get("workshop_id")
    if target_workshop_id:
        selected_workshop = mongo.db.workshops.find_one({"_id": ObjectId(target_workshop_id)})
        
    return render_template("user/request_service.html", user=user, selected_workshop=selected_workshop)



# ─── Track Request ────────────────────────────────────────────────────────────
@user_bp.route("/track/<request_id>")
@login_required
def track_request(request_id):
    req = mongo.db.service_requests.find_one({
        "_id": ObjectId(request_id),
        "user_id": ObjectId(session["user_id"]),
    })
    if not req:
        flash("Request not found.", "danger")
        return redirect(url_for("user.dashboard"))

    mechanic = None
    workshop = None
    if req.get("assigned_mechanic_id"):
        mechanic = mongo.db.mechanics.find_one({"_id": req["assigned_mechanic_id"]})
    if req.get("workshop_id"):
        workshop = mongo.db.workshops.find_one({"_id": req["workshop_id"]})

    return render_template("user/track_request.html", req=req, mechanic=mechanic, workshop=workshop)


# ─── Nearby Workshops ─────────────────────────────────────────────────────────
@user_bp.route("/nearby_workshops", methods=["GET"])
@login_required
def nearby_workshops():
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    if not lat or not lng:
        return jsonify({"error": "Missing coordinates"}), 400
    try:
        workshops = list(
            mongo.db.workshops.find({
                "location": {
                    "$near": {
                        "$geometry": {"type": "Point", "coordinates": [float(lng), float(lat)]},
                        "$maxDistance": 30000,
                    }
                }
            }).limit(10)
        )
        result = []
        for w in workshops:
            result.append({
                "id": str(w["_id"]),
                "name": w.get("name"),
                "location_name": w.get("location_name"),
                "email": w.get("email"),
                "phone": w.get("phone", ""),
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─── Vehicle & Profile Management ─────────────────────────────────────────────
@user_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_vehicle":
            v_type = request.form.get("vehicle_type", "").strip()
            company = request.form.get("vehicle_company", "").strip()
            model = request.form.get("vehicle_model", "").strip()
            year = request.form.get("vehicle_year", "").strip()
            
            new_vehicle = {
                "type": v_type,
                "company": company,
                "model": model,
                "year": year, 
                "added_at": datetime.utcnow()
            }
            mongo.db.users.update_one(
                {"_id": ObjectId(session["user_id"])},
                {"$push": {"vehicles": new_vehicle}}
            )
            flash("Vehicle added successfully.", "success")
            
        elif action == "delete_vehicle":
            idx = int(request.form.get("vehicle_index", -1))
            if "vehicles" in user and 0 <= idx < len(user["vehicles"]):
                vehicles = user["vehicles"]
                vehicles.pop(idx)
                mongo.db.users.update_one(
                    {"_id": ObjectId(session["user_id"])},
                    {"$set": {"vehicles": vehicles}}
                )
                flash("Vehicle deleted.", "info")
                
        return redirect(url_for("user.profile"))
        
    return render_template("user/profile.html", user=user)

# ─── Cancel Request ───────────────────────────────────────────────────────────
@user_bp.route("/request/cancel/<request_id>", methods=["POST"])
@login_required
def cancel_request(request_id):
    req = mongo.db.service_requests.find_one({
        "_id": ObjectId(request_id),
        "user_id": ObjectId(session["user_id"])
    })
    if not req:
        flash("Request not found.", "danger")
        return redirect(url_for("user.dashboard"))
        
    if req.get("status") != "Pending":
        flash("Cannot cancel a request that has already been accepted.", "warning")
        return redirect(url_for("user.dashboard"))
        
    if datetime.utcnow() - req["created_at"] > timedelta(minutes=5):
        flash("Cancellation window (5 minutes) has expired. Please contact the workshop directly.", "danger")
        return redirect(url_for("user.dashboard"))
        
    mongo.db.service_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"status": "Cancelled"}}
    )
    flash("Service request cancelled successfully.", "success")
    return redirect(url_for("user.dashboard"))

