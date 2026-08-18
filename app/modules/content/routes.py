# app/modules/content/routes.py
from . import content_bp

@content_bp.route('/')
def index():
    return 'Content module — en construcción'