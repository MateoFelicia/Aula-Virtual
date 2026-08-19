# app/modules/content/routes.py
from . import content_bp
from .models import Material  # noqa: F401 - registra el modelo en SQLAlchemy aunque no se use todavía

@content_bp.route('/')
def index():
    return 'Content module — en construcción'