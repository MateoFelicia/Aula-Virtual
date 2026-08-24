# app/config.py
"""
Configuración por entorno. Usamos el patrón de clases que
recomienda la propia documentación de Flask para no repetir
config entre desarrollo/testing/producción.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # lee el archivo .env si existe

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Config base: lo que comparten todos los entornos."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-provisoria-cambiar-en-.env')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB máx por archivo subido

    # BDD PROVISORIA: SQLite mientras MySQL no esté disponible.
    # Vive en la raíz del proyecto (junto a run.py).
    SQLITE_DEV_DB = 'sqlite:///' + os.path.join(
        os.path.dirname(basedir), 'aula_virtual_dev.db'
    )

    # Confirmación de email
    CONFIRM_TOKEN_MAX_AGE = 60 * 60 * 24  # el link vale 24 horas
    # Base para armar los links que van en los emails (cambiar en .env
    # cuando se deploye a un dominio real)
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5001')

    # Envío de emails. Si MAIL_SERVER no está definido en el .env,
    # no se manda nada real: el link de confirmación se imprime por consola.
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get(
        'MAIL_DEFAULT_SENDER', 'no-reply@aula-virtual.local'
    )
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'


class DevelopmentConfig(Config):
    DEBUG = True
    # Si DATABASE_URL está definida en el .env se usa esa (ej: MySQL),
    # si no, cae al SQLite provisorio.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        Config.SQLITE_DEV_DB
    )


class TestingConfig(Config):
    TESTING = True
    # SQLite en memoria para tests: rápido y no ensucia la BDD real
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False  # simplifica los tests de formularios


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}