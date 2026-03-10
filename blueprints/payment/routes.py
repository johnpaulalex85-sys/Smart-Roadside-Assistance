from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import mongo
from bson import ObjectId
from datetime import datetime
from utils.notifications import send_email_notification

payment_bp = Blueprint("payment", __name__, url_prefix="/payment")

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to process payments.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

@payment_bp.route("/checkout/<request_id>", methods=["GET", "POST"])
@login_required
def checkout(request_id):
    req = mongo.db.service_requests.find_one({"_id": ObjectId(request_id), "user_id": ObjectId(session["user_id"])})
    if not req:
        flash("Request not found.", "danger")
        return redirect(url_for("user.dashboard"))
        
    if request.method == "POST":
        # Simulate payment processing
        payment_method = request.form.get("payment_method", "Credit Card")
        
        # Update request
        mongo.db.service_requests.update_one(
            {"_id": ObjectId(request_id)},
            {"₹set": {
                "payment_status": "Completed",
                "payment_id": f"txn_{ObjectId()}",
                "payment_method": payment_method,
                "paid_at": datetime.utcnow()
            }}
        )
        
        user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})
        if user and user.get("email"):
            send_email_notification(user["email"], "Payment Receipt - Smart Roadside Assistance", f"Your payment of ₹{req.get('estimated_cost', 0):.2f} was successful.")
            
        flash("Payment successful! Please rate the service.", "success")
        return redirect(url_for("payment.rate_service", request_id=request_id))
        
    workshop = mongo.db.workshops.find_one({"_id": req.get("workshop_id")})
    return render_template("payment/checkout.html", req=req, workshop=workshop)

@payment_bp.route("/rate/<request_id>", methods=["GET", "POST"])
@login_required
def rate_service(request_id):
    req = mongo.db.service_requests.find_one({"_id": ObjectId(request_id), "user_id": ObjectId(session["user_id"])})
    
    if request.method == "POST":
        workshop_rating = int(request.form.get("workshop_rating", 5))
        mechanic_rating = int(request.form.get("mechanic_rating", 5))
        feedback = request.form.get("feedback_text", "")
        
        mongo.db.service_requests.update_one(
            {"_id": ObjectId(request_id)},
            {"₹set": {
                "workshop_rating": workshop_rating,
                "mechanic_rating": mechanic_rating,
                "feedback_text": feedback
            }}
        )
        flash("Thank you for your feedback!", "success")
        return redirect(url_for("user.dashboard"))
        
    return render_template("payment/rate_service.html", req=req)
