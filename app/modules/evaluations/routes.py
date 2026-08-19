# app/modules/evaluations/routes.py
from . import evaluations_bp
from .models import Exam  # noqa: F401 - registra el modelo en SQLAlchemy aunque no se use todavía

@evaluations_bp.route('/')
def index():
    return 'Evaluations module — en construcción'