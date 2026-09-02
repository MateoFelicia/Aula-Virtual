# app/modules/schools/services.py
"""
Servicio del módulo de colegios.

Centraliza toda la lógica de negocio:
  - Crear colegio (el creador queda como admin + alumno).
  - Unirse a colegio con código.
  - Gestionar miembros (agregar/quitar profesores y alumnos).
  - Promover/degradar roles.
"""
from app.core.base_service import BaseService
from app.extensions import db
from .models import School, SchoolMember, SchoolRole
from app.modules.auth.models import User


class SchoolService(BaseService):
    model = School

    @classmethod
    def create_school(cls, name, description, admin_user):
        code = School.generate_code()
        while School.query.filter_by(code=code).first():
            code = School.generate_code()

        school = School(
            name=name,
            description=description or None,
            admin_id=admin_user.id,
            code=code
        )
        school.save()

        member = SchoolMember(
            school_id=school.id,
            user_id=admin_user.id,
            role=SchoolRole.ADMIN
        )
        member.save()

        return school

    @classmethod
    def join_school(cls, code, user):
        school = School.query.filter_by(code=code).first()
        if not school:
            return None, 'No se encontró un colegio con ese código.'

        existing = SchoolMember.query.filter_by(
            school_id=school.id,
            user_id=user.id
        ).first()
        if existing:
            return None, 'Ya pertenecés a este colegio.'

        member = SchoolMember(
            school_id=school.id,
            user_id=user.id,
            role=SchoolRole.ALUMNO
        )
        member.save()

        return school, None

    @classmethod
    def get_user_schools(cls, user):
        memberships = SchoolMember.query.filter_by(user_id=user.id).all()
        return [m.school for m in memberships]

    @classmethod
    def promote_to_profesor(cls, school_id, user_id):
        member = SchoolMember.query.filter_by(
            school_id=school_id,
            user_id=user_id
        ).first()
        if not member:
            return False, 'Miembro no encontrado.'
        member.role = SchoolRole.PROFESOR
        db.session.commit()
        return True, None

    @classmethod
    def demote_to_alumno(cls, school_id, user_id):
        member = SchoolMember.query.filter_by(
            school_id=school_id,
            user_id=user_id
        ).first()
        if not member:
            return False, 'Miembro no encontrado.'
        member.role = SchoolRole.ALUMNO
        db.session.commit()
        return True, None

    @classmethod
    def remove_member(cls, school_id, user_id):
        member = SchoolMember.query.filter_by(
            school_id=school_id,
            user_id=user_id
        ).first()
        if not member:
            return False, 'Miembro no encontrado.'
        member.delete()
        return True, None

    @classmethod
    def add_member_by_email(cls, school_id, email, role=SchoolRole.ALUMNO):
        user = User.query.filter_by(email=email).first()
        if not user:
            return None, 'No se encontró un usuario con ese email.'

        existing = SchoolMember.query.filter_by(
            school_id=school_id,
            user_id=user.id
        ).first()
        if existing:
            return None, 'Ese usuario ya pertenece al colegio.'

        member = SchoolMember(
            school_id=school_id,
            user_id=user.id,
            role=role
        )
        member.save()

        return member, None
