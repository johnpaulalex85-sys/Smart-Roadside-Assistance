from extensions import mongo
from werkzeug.security import generate_password_hash, check_password_hash



def create_workshop(name, email, password, phone, location_name, longitude, latitude):
    workshop = {
        "name": name,
        "email": email,
        "password": generate_password_hash(password),
        "phone": phone,
        "location_name": location_name,
        "location": {
            "type": "Point",
            "coordinates": [float(longitude), float(latitude)],
        },
        "role": "workshop",
    }
    result = mongo.db.workshops.insert_one(workshop)
    return result.inserted_id


def find_workshop_by_email(email):
    return mongo.db.workshops.find_one({"email": email})


def find_workshop_by_id(workshop_id):
    from bson import ObjectId
    return mongo.db.workshops.find_one({"_id": ObjectId(workshop_id)})


def verify_password(workshop, password):
    return check_password_hash(workshop["password"], password)


def get_all_workshops():
    return list(mongo.db.workshops.find())


def find_nearest_workshops(longitude, latitude, max_distance=10000):
    """Find workshops within max_distance metres using $near."""
    return list(
        mongo.db.workshops.find(
            {
                "location": {
                    "$near": {
                        "$geometry": {
                            "type": "Point",
                            "coordinates": [float(longitude), float(latitude)],
                        },
                        "$maxDistance": max_distance,
                    }
                }
            }
        ).limit(10)
    )
