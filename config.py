import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "road_rescue_super_secret_key_2024")
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://mechanicaluser:kolonia%40123@cluster0.7lpf3re.mongodb.net/road_rescue?appName=Cluster0")
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "mp4"}
    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "YOUR_GOOGLE_MAPS_API_KEY")
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
