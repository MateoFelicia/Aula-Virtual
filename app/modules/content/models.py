# app/modules/content/models.py
"""
Modelo Material — representa un archivo o enlace subido por un profesor
a un curso determinado.

Tipos soportados (material_type):
  - 'file'  → se guarda un archivo físico en UPLOAD_FOLDER
  - 'link'  → se guarda una URL externa (YouTube, Drive, etc.)

El campo file_path guarda:
  - Para tipo 'file': la ruta relativa dentro de uploads/ (ej: "curso_1/clase2.pdf")
  - Para tipo 'link': None (la URL está en external_url)
"""
from app.extensions import db
from app.core.base_model import BaseModel


class Material(BaseModel):
    __tablename__ = 'materials'

    # FK al curso al que pertenece este material
    course_id = db.Column(
        db.Integer,
        db.ForeignKey('courses.id'),
        nullable=False
    )

    # Título descriptivo del material
    title = db.Column(db.String(150), nullable=False)

    # Descripción opcional (qué contiene, qué tema cubre, etc.)
    description = db.Column(db.Text, nullable=True)

    # Tipo de material: 'file' o 'link'
    # Usamos String en vez de Enum para compatibilidad con MySQL sin
    # tener que definir un tipo Enum en la base.
    material_type = db.Column(db.String(10), nullable=False, default='file')

    # Ruta del archivo subido (solo para material_type='file').
    # Se guarda relativa a UPLOAD_FOLDER, ej: "1/mi_archivo.pdf"
    file_path = db.Column(db.String(255), nullable=True)

    # URL externa (solo para material_type='link').
    # Ej: "https://www.youtube.com/watch?v=..."
    external_url = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f'<Material {self.title} ({self.material_type})>'
