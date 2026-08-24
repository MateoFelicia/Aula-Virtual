# app/modules/auth/mailer.py
"""
Envío de emails del módulo auth.

Si hay MAIL_SERVER configurado (en el .env) manda un mail real vía SMTP.
Si no, "envía" el mail imprimiendo el contenido por consola — así el flujo
de confirmación es 100% probable en desarrollo sin cuenta de correo.
"""
import logging
import smtplib

from flask import current_app
from email.mime.text import MIMEText


def _external_link(endpoint, **values):
    """
    Arma un link absoluto usando BASE_URL de la config, sin depender de
    SERVER_NAME (que si se setea, rompe requests que entren por otro host,
    ej: 127.0.0.1 en vez de localhost).
    """
    base = current_app.config['BASE_URL'].rstrip('/')
    host = base.split('//', 1)[-1]  # url_map.bind quiere solo host:puerto
    path = current_app.url_map.bind(host).build(endpoint, values=values)
    return base + path


def send_confirmation_email(user, token):
    link = _external_link('auth.confirm', token=token)
    body = (
        f"Hola {user.first_name},\n\n"
        f"Confirmá tu cuenta entrando a este link:\n{link}\n\n"
        f"El link vence en 24 horas.\n\n"
        f"— Aula Virtual"
    )

    if current_app.config.get('MAIL_SERVER'):
        _send_via_smtp(user.email, 'Confirmá tu cuenta - Aula Virtual', body)
    else:
        # Modo desarrollo: sin SMTP configurado. print en vez del logger
        # para que el link se vea siempre, sin importar el nivel de logs.
        print(
            '\n===== EMAIL (modo consola) ====='
            f'\nPara: {user.email}'
            '\nAsunto: Confirmá tu cuenta - Aula Virtual'
            f'\n{body}'
            '\n================================',
            flush=True
        )


def _send_via_smtp(to, subject, body):
    cfg = current_app.config
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = cfg['MAIL_DEFAULT_SENDER']
    msg['To'] = to

    with smtplib.SMTP(cfg['MAIL_SERVER'], cfg['MAIL_PORT']) as server:
        if cfg['MAIL_USE_TLS']:
            server.starttls()
        if cfg['MAIL_USERNAME'] and cfg['MAIL_PASSWORD']:
            server.login(cfg['MAIL_USERNAME'], cfg['MAIL_PASSWORD'])
        server.sendmail(cfg['MAIL_DEFAULT_SENDER'], [to], msg.as_string())

    logging.getLogger(__name__).info('Email de confirmación enviado a %s', to)
