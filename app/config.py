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


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'mysql+pymysql://root:password@localhost/aula_virtual_dev'
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