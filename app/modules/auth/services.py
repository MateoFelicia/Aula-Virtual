# app/modules/auth/services.py
from app.core.base_service import BaseService
from .models import User


class AuthService(BaseService):
    model = User

    @classmethod
    def register(cls, first_name, last_name, email, password, role):
        if User.query.filter_by(email=email).first():
            raise ValueError('Ya existe una cuenta con ese email')

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role
        )
        user.set_password(password)
        return user.save()

    @classmethod
    def authenticate(cls, email, password):
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            return user
        return None