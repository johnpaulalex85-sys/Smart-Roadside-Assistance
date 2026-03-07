from extensions import mongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId



def create_mechanic(name, email, password, workshop_id):
    mechanic = {
        "name": name,
        "email": email,
        "password": generate_password_hash(password),
        "workshop_id": ObjectId(workshop_id),
        "status": "available",
        "role": "mechanic",
    }
    result = mongo.db.mechanics.insert_one(mechanic)
    return result.inserted_id


def find_mechanic_by_email(email):
    return mongo.db.mechanics.find_one({"email": email})


def find_mechanic_by_id(mechanic_id):
    return mongo.db.mechanics.find_one({"_id": ObjectId(mechanic_id)})


def verify_password(mechanic, password):
    return check_password_hash(mechanic["password"], password)


def get_mechanics_by_workshop(workshop_id):
    return list(mongo.db.mechanics.find({"workshop_id": ObjectId(workshop_id)}))


def get_available_mechanics(workshop_id):
    return list(
        mongo.db.mechanics.find(
            {"workshop_id": ObjectId(workshop_id), "status": "available"}
        )
    )


def get_all_mechanics():
    return list(mongo.db.mechanics.find())
