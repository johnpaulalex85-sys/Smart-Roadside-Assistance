from flask import Blueprint

mechanic_bp = Blueprint("mechanic", __name__, template_folder="../../templates/mechanic")

from blueprints.mechanic import routes  # noqa: F401, E402
