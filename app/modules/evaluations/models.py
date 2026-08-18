# app/modules/evaluations/models.py
from app.extensions import db
from app.core.base_model import BaseModel

class Exam(BaseModel):
    __tablename__ = 'exams'
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)