# app/modules/auth/models.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager
from app.core.base_model import BaseModel


class Role:
    """No es tabla, son constantes — evita strings mágicos regados por el código."""
    ADMIN = 'admin'
    PROFESOR = 'profesor'
    ALUMNO = 'alumno'


class User(BaseModel, UserMixin):
    __tablename__ = 'users'

    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=Role.ALUMNO)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_profesor(self):
        return self.role == Role.PROFESOR

    def is_alumno(self):
        return self.role == Role.ALUMNO

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login necesita esta función para recuperar el user desde la sesión."""
    return User.query.get(int(user_id))