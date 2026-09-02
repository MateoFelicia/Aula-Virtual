# app/modules/courses/models.py
"""
Modelos del módulo de cursos.

Course: representa un curso dentro de un colegio.
  - Pertenecen a un colegio (school_id).
  - Se unen con código (course_code) estilo Classroom.
  - No tienen un profesor fijo: los profesores del colegio acceden a todos los cursos.

CourseMember: vincula un usuario con un curso y define su rol.
  - profesor: puede gestionar el curso (materiales, evaluaciones).
  - alumno: se inscribió con el código del curso.
"""
import secrets
from app.extensions import db
from app.core.base_model import BaseModel


class Course(BaseModel):
    __tablename__ = 'courses'

    school_id = db.Column(
        db.Integer,
        db.ForeignKey('schools.id'),
        nullable=False
    )

    title = db.Column(db.String(150), nullable=False)

    description = db.Column(db.Text, nullable=True)

    capacity = db.Column(db.Integer, nullable=True)

    course_code = db.Column(db.String(10), unique=True, nullable=False, index=True)

    members = db.relationship(
        'CourseMember',
        backref='course',
        lazy=True,
        cascade='all, delete-orphan'
    )

    materials = db.relationship(
        'Material',
        backref='course',
        lazy='dynamic'
    )

    @staticmethod
    def generate_code():
        return secrets.token_urlsafe(5).upper()

    def get_member(self, user):
        return CourseMember.query.filter_by(
            course_id=self.id,
            user_id=user.id
        ).first()

    def is_member(self, user):
        return self.get_member(user) is not None

    def is_profesor(self, user):
        member = self.get_member(user)
        return member is not None and member.role == CourseMemberRole.PROFESOR

    def is_alumno(self, user):
        member = self.get_member(user)
        return member is not None and member.role == CourseMemberRole.ALUMNO

    def is_full(self):
        if self.capacity is None:
            return False
        return self.enrolled_count() >= self.capacity

    def enrolled_count(self):
        return CourseMember.query.filter_by(
            course_id=self.id,
            role=CourseMemberRole.ALUMNO
        ).count()

    def __repr__(self):
        return f'<Course {self.title}>'


class CourseMemberRole:
    PROFESOR = 'profesor'
    ALUMNO = 'alumno'


class CourseMember(BaseModel):
    __tablename__ = 'course_members'

    course_id = db.Column(
        db.Integer,
        db.ForeignKey('courses.id'),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    role = db.Column(db.String(20), nullable=False, default=CourseMemberRole.ALUMNO)

    user = db.relationship(
        'User',
        backref=db.backref('course_memberships', lazy=True)
    )

    __table_args__ = (
        db.UniqueConstraint('course_id', 'user_id', name='uq_course_user'),
    )

    def __repr__(self):
        return f'<CourseMember course={self.course_id} user={self.user_id} role={self.role}>'
