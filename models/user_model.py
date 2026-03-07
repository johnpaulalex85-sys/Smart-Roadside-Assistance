from datetime import datetime
from extensions import mongo

from werkzeug.security import generate_password_hash, check_password_hash


def create_user(name, email, password, phone):
    user = {
        "name": name,
        "email": email,
        "password": generate_password_hash(password),
        "phone": phone,
        "role": "user",
        "created_at": datetime.utcnow(),
    }
    result = mongo.db.users.insert_one(user)
    return result.inserted_id


def find_user_by_email(email):
    return mongo.db.users.find_one({"email": email})


def find_user_by_id(user_id):
    from bson import ObjectId
    return mongo.db.users.find_one({"_id": ObjectId(user_id)})


def verify_password(user, password):
    return check_password_hash(user["password"], password)


def get_all_users():
    return list(mongo.db.users.find())
