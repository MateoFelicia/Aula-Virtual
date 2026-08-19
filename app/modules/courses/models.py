# app/modules/courses/models.py
"""
Modelos del módulo de cursos.

Course: representa un curso creado por un profesor.
Enrollment: representa la inscripción de un alumno a un curso.
  - unique_together en (course_id, student_id) evita que un alumno
    se inscriba dos veces al mismo curso.
"""
from app.extensions import db
from app.core.base_model import BaseModel


class Course(BaseModel):
    __tablename__ = 'courses'

    # Título corto del curso (obligatorio)
    title = db.Column(db.String(150), nullable=False)

    # Descripción libre — puede quedarse vacía al crear y completarse después
    description = db.Column(db.Text, nullable=True)

    # Capacidad máxima de alumnos (NULL = sin límite)
    capacity = db.Column(db.Integer, nullable=True)

    # FK al usuario que creó el curso (debe ser profesor).
    # backref='instructed_courses' me permite hacer course.instructor
    # y también user.instructed_courses desde el lado del usuario.
    instructor_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    # Relación bidireccional: course.instructor devuelve el User
    instructor = db.relationship('User', backref=db.backref('instructed_courses', lazy=True))

    # Relación 1 a N: un curso tiene muchas inscripciones
    enrollments = db.relationship('Enrollment', backref='course', lazy=True, cascade='all, delete-orphan')

    # Relación 1 a N: un curso tiene muchos materiales (módulo content)
    # lazy='dynamic' porque pueden ser muchos y conviene paginar
    materials = db.relationship('Material', backref='course', lazy='dynamic')

    def is_full(self):
        """Devuelve True si el curso alcanzó su capacidad máxima."""
        if self.capacity is None:
            return False
        return len(self.enrollments) >= self.capacity

    def enrolled_count(self):
        """Cantidad actual de alumnos inscriptos."""
        return len(self.enrollments)

    def is_enrolled(self, user):
        """Devuelve True si el usuario dado está inscripto en este curso."""
        return Enrollment.query.filter_by(
            course_id=self.id,
            student_id=user.id
        ).first() is not None

    def __repr__(self):
        return f'<Course {self.title}>'


class Enrollment(BaseModel):
    __tablename__ = 'enrollments'

    # FK al curso al que se inscribe el alumno
    course_id = db.Column(
        db.Integer,
        db.ForeignKey('courses.id'),
        nullable=False
    )

    # FK al alumno que se inscribe
    student_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    # Relación bidireccional: enrollment.student devuelve el User
    student = db.relationship('User', backref=db.backref('enrollments', lazy=True))

    # Evita inscripción duplicada: no puede haber dos filas con
    # el mismo course_id + student_id en la tabla.
    __table_args__ = (
        db.UniqueConstraint('course_id', 'student_id', name='uq_course_student'),
    )

    def __repr__(self):
        return f'<Enrollment course={self.course_id} student={self.student_id}>'