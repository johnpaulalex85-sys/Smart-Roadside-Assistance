from flask import Blueprint

user_bp = Blueprint("user", __name__, template_folder="../../templates/user")

from blueprints.user import routes  # noqa: F401, E402
