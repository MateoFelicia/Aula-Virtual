# Extensiones de Flask
"""
Instancias de extensiones de Flask, desacopladas de la app.
Se inicializan de verdad recién en create_app() (app/__init__.py).
Esto evita imports circulares entre modules/*.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

# Configuración de Flask-Login: a dónde redirige si alguien
# no logueado intenta acceder a una ruta protegida
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor iniciá sesión para acceder a esta página.'
login_manager.login_message_category = 'info'