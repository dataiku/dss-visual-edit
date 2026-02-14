from flask import Blueprint

from .config import config_blueprint
from .editlogs import editlogs_blueprint
from .layout import layout_blueprint
from .linked_dataset import linked_dataset_blueprint

api = Blueprint("api", __name__, url_prefix="/api")

api.register_blueprint(editlogs_blueprint)
api.register_blueprint(layout_blueprint)
api.register_blueprint(linked_dataset_blueprint)
api.register_blueprint(config_blueprint)
