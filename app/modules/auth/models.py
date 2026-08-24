# app/modules/auth/models.py
from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager
from app.core.base_model import BaseModel

# Salt fijo para que los tokens de email no se puedan reutilizar en
# otro contexto firmado con la misma SECRET_KEY (ej: reset de password)
CONFIRM_SALT = 'confirmar-email'


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
    email_confirmed = db.Column(db.Boolean, nullable=False, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_profesor(self):
        return self.role == Role.PROFESOR

    def is_alumno(self):
        return self.role == Role.ALUMNO

    # ---- Confirmación de email ----

    def generate_confirmation_token(self):
        """Token firmado y con vencimiento que identifica a este usuario."""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=CONFIRM_SALT)
        return s.dumps(self.id)

    @classmethod
    def find_by_confirmation_token(cls, token):
        """
        Verifica el token y devuelve el usuario correspondiente.
        Devuelve None si el token es inválido o ya expiró.
        """
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=CONFIRM_SALT)
        try:
            user_id = s.loads(
                token,
                max_age=current_app.config['CONFIRM_TOKEN_MAX_AGE']
            )
        except (SignatureExpired, BadSignature):
            return None
        return cls.query.get(int(user_id))

    def confirm_email(self):
        self.email_confirmed = True
        db.session.commit()

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login necesita esta función para recuperar el user desde la sesión."""
    return User.query.get(int(user_id))