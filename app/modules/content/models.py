# app/modules/content/models.py
from app.extensions import db
from app.core.base_model import BaseModel

class Material(BaseModel):
    __tablename__ = 'materials'
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    file_path = db.Column(db.String(255))