# app/modules/evaluations/__init__.py
from flask import Blueprint

evaluations_bp = Blueprint('evaluations', __name__, url_prefix='/evaluations')

from . import routes