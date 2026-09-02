# app/modules/schools/models.py
"""
Modelos del módulo de colegios.

School: representa un colegio/institución. Quien lo crea queda como admin.
SchoolMember: vincula un usuario con un colegio y define su rol dentro de él.
  - admin: creó el colegio, gestiona miembros.
  - profesor: puede crear y gestionar cursos dentro del colegio.
  - alumno: se incorpora a cursos mediante código.

La identidad es del usuario; el rol depende del colegio.
"""
import secrets
from app.extensions import db
from app.core.base_model import BaseModel


class School(BaseModel):
    __tablename__ = 'schools'

    name = db.Column(db.String(150), nullable=False)

    code = db.Column(db.String(10), unique=True, nullable=False, index=True)

    description = db.Column(db.Text, nullable=True)

    admin_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    admin = db.relationship(
        'User',
        backref=db.backref('administered_schools', lazy=True)
    )

    members = db.relationship(
        'SchoolMember',
        backref='school',
        lazy=True,
        cascade='all, delete-orphan'
    )

    courses = db.relationship(
        'Course',
        backref='school',
        lazy=True,
        cascade='all, delete-orphan'
    )

    @staticmethod
    def generate_code():
        return secrets.token_urlsafe(6).upper()

    def get_member(self, user):
        return SchoolMember.query.filter_by(
            school_id=self.id,
            user_id=user.id
        ).first()

    def is_member(self, user):
        return self.get_member(user) is not None

    def is_admin(self, user):
        member = self.get_member(user)
        return member is not None and member.role == SchoolRole.ADMIN

    def is_profesor(self, user):
        member = self.get_member(user)
        return member is not None and member.role == SchoolRole.PROFESOR

    def is_alumno(self, user):
        member = self.get_member(user)
        return member is not None and member.role == SchoolRole.ALUMNO

    def __repr__(self):
        return f'<School {self.name}>'


class SchoolRole:
    ADMIN = 'admin'
    PROFESOR = 'profesor'
    ALUMNO = 'alumno'


class SchoolMember(BaseModel):
    __tablename__ = 'school_members'

    school_id = db.Column(
        db.Integer,
        db.ForeignKey('schools.id'),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    role = db.Column(db.String(20), nullable=False, default=SchoolRole.ALUMNO)

    user = db.relationship(
        'User',
        backref=db.backref('school_memberships', lazy=True)
    )

    __table_args__ = (
        db.UniqueConstraint('school_id', 'user_id', name='uq_school_user'),
    )

    def __repr__(self):
        return f'<SchoolMember school={self.school_id} user={self.user_id} role={self.role}>'
