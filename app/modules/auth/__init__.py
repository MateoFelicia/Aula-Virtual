# app/modules/auth/__init__.py
"""
Blueprint del módulo auth. Cada módulo se registra como un
blueprint independiente — esto es lo que en la práctica separa
"servicios" dentro del mismo proceso Flask.
"""
from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

from . import routes  # importa al final para evitar imports circulares