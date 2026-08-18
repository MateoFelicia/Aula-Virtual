# app/modules/evaluations/routes.py
from . import evaluations_bp

@evaluations_bp.route('/')
def index():
    return 'Evaluations module — en construcción'