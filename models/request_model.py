from datetime import datetime
from extensions import mongo
from bson import ObjectId



def create_request(user_id, vehicle_type, vehicle_company, vehicle_model,
                   vehicle_year, description, media):
    request = {
        "user_id": ObjectId(user_id),
        "workshop_id": None,
        "assigned_mechanic_id": None,
        "vehicle_type": vehicle_type,
        "vehicle_company": vehicle_company,
        "vehicle_model": vehicle_model,
        "vehicle_year": vehicle_year,
        "description": description,
        "media": media,
        "status": "Pending",
        "created_at": datetime.utcnow(),
    }
    result = mongo.db.service_requests.insert_one(request)
    return result.inserted_id


def get_requests_by_user(user_id):
    return list(
        mongo.db.service_requests.find({"user_id": ObjectId(user_id)}).sort("created_at", -1)
    )


def get_pending_requests():
    return list(
        mongo.db.service_requests.find({"status": "Pending"}).sort("created_at", -1)
    )


def get_requests_by_workshop(workshop_id):
    return list(
        mongo.db.service_requests.find({"workshop_id": ObjectId(workshop_id)}).sort("created_at", -1)
    )


def get_requests_by_mechanic(mechanic_id):
    return list(
        mongo.db.service_requests.find({"assigned_mechanic_id": ObjectId(mechanic_id)}).sort("created_at", -1)
    )


def get_request_by_id(request_id):
    return mongo.db.service_requests.find_one({"_id": ObjectId(request_id)})


def update_request_status(request_id, status):
    mongo.db.service_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"status": status}},
    )


def accept_request(request_id, workshop_id):
    mongo.db.service_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"workshop_id": ObjectId(workshop_id), "status": "Accepted"}},
    )


def assign_mechanic(request_id, mechanic_id):
    mongo.db.service_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"assigned_mechanic_id": ObjectId(mechanic_id), "status": "Assigned"}},
    )


def get_all_requests():
    return list(mongo.db.service_requests.find().sort("created_at", -1))
