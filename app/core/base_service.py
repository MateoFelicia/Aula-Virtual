# app/core/base_service.py
"""
Clase base para la capa de servicios. Las rutas NUNCA hablan
directo con los modelos ni con db.session — siempre pasan por
un Service. Esto centraliza la lógica de negocio y hace que
todo sea testeable sin levantar un servidor HTTP.
"""
from app.extensions import db


class BaseService:
    model = None  # cada subclase define a qué modelo apunta

    @classmethod
    def get_by_id(cls, id):
        return cls.model.query.get_or_404(id)

    @classmethod
    def get_all(cls):
        return cls.model.query.all()

    @classmethod
    def create(cls, **kwargs):
        instance = cls.model(**kwargs)
        return instance.save()

    @classmethod
    def update(cls, id, **kwargs):
        instance = cls.get_by_id(id)
        for key, value in kwargs.items():
            setattr(instance, key, value)
        db.session.commit()
        return instance

    @classmethod
    def delete(cls, id):
        instance = cls.get_by_id(id)
        instance.delete()
        return True