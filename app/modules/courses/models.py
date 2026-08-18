# app/modules/courses/models.py
from app.extensions import db
from app.core.base_model import BaseModel

class Course(BaseModel):
    __tablename__ = 'courses'
    # TODO: title, description, instructor_id (FK a users), capacity...

class Enrollment(BaseModel):
    __tablename__ = 'enrollments'
    # TODO: course_id (FK), student_id (FK)... ¡y unique_together para evitar doble inscripción!