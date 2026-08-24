# app/modules/auth/services.py
import logging

from flask import current_app

from app.core.base_service import BaseService
from .mailer import send_confirmation_email
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

    # ---- Confirmación de email ----

    @classmethod
    def send_confirmation(cls, user):
        """
        Genera el token y manda el mail con el link de confirmación.
        Si el envío falla (SMTP caído, clave mal puesta, etc.) no revienta:
        devuelve False para que la ruta avise y se pueda reenviar.
        """
        try:
            token = user.generate_confirmation_token()
            send_confirmation_email(user, token)
            return True
        except Exception:
            logging.getLogger(__name__).exception(
                'No se pudo enviar el email de confirmación a %s', user.email
            )
            return False

    @classmethod
    def confirm_email(cls, token):
        """
        Confirma la cuenta si el token es válido.
        Devuelve (usuario, mensaje). El usuario es None si el token
        es inválido/expirado.
        """
        user = User.find_by_confirmation_token(token)
        if user is None:
            return None, 'El link es inválido o ya expiró. Pedí uno nuevo.'

        if user.email_confirmed:
            return user, 'Tu email ya estaba confirmado. Iniciá sesión.'

        user.confirm_email()
        return user, '¡Email confirmado! Ya podés iniciar sesión.'

    @classmethod
    def resend_confirmation(cls, email):
        """
        Reenvía el mail de confirmación. Para no revelar qué emails
        están registrados, responde lo mismo exista o no la cuenta.
        """
        user = User.query.filter_by(email=email).first()
        if user and not user.email_confirmed:
            cls.send_confirmation(user)