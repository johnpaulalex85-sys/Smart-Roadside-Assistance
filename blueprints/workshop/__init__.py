from flask import Blueprint

workshop_bp = Blueprint("workshop", __name__, template_folder="../../templates/workshop")

from blueprints.workshop import routes  # noqa: F401, E402
