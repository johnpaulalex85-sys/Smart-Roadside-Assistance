import os
from flask import Flask
from config import Config
from extensions import mongo
from werkzeug.security import generate_password_hash


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    mongo.init_app(app)

    # Create 2dsphere index for workshops + seed default admin
    with app.app_context():
        try:
            mongo.db.workshops.create_index([("location", "2dsphere")])
        except Exception:
            pass

        # Seed default admin account
        if not mongo.db.admins.find_one({"email": "admin@smartroadsideassistance.com"}):
            mongo.db.admins.insert_one({
                "email": "admin@smartroadsideassistance.com",
                "name": "Super Admin",
                "password": generate_password_hash("Admin@1234"),
                "role": "admin",
            })

    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.user import user_bp
    from blueprints.workshop import workshop_bp
    from blueprints.mechanic import mechanic_bp
    from blueprints.admin import admin_bp
    from blueprints.payment.routes import payment_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(workshop_bp, url_prefix="/workshop")
    app.register_blueprint(mechanic_bp, url_prefix="/mechanic")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(payment_bp)

    # Root redirect
    from flask import redirect, url_for

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
