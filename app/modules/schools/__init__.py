# app/modules/schools/__init__.py
from flask import Blueprint

schools_bp = Blueprint('schools', __name__, url_prefix='/schools')

from . import routes
