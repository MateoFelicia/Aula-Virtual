# app/core/base_model.py
"""
Mixin base para todos los modelos. Cualquier modelo que herede
de esto obtiene automáticamente id, timestamps y un método
serialize() por defecto (útil para debug o futuras APIs JSON).
"""
from datetime import datetime
from app.extensions import db


class BaseModel(db.Model):
    __abstract__ = True  # SQLAlchemy no crea tabla para esta clase

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def serialize(self):
        """Serialización genérica; cada modelo puede sobreescribirla."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}