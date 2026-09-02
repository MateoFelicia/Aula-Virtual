# app/modules/courses/services.py
"""
Servicio del módulo de cursos.

Centraliza la lógica de negocio:
  - Crear curso (requiere ser profesor en el colegio).
  - Unirse a curso con código.
  - Gestionar alumnos del curso.
  - Listar cursos por colegio.
"""
from app.core.base_service import BaseService
from app.extensions import db
from .models import Course, CourseMember, CourseMemberRole
from app.modules.schools.models import School, SchoolMember, SchoolRole


class CourseService(BaseService):
    model = Course

    @classmethod
    def create_course(cls, school_id, title, description, capacity, creator_user):
        school = School.query.get_or_404(school_id)

        member = SchoolMember.query.filter_by(
            school_id=school_id,
            user_id=creator_user.id
        ).first()
        if not member or member.role not in (SchoolRole.ADMIN, SchoolRole.PROFESOR):
            return None, 'No tenés permiso para crear cursos en este colegio.'

        code = Course.generate_code()
        while Course.query.filter_by(course_code=code).first():
            code = Course.generate_code()

        course = Course(
            school_id=school_id,
            title=title,
            description=description or None,
            capacity=capacity if capacity else None,
            course_code=code
        )
        course.save()

        prof_member = CourseMember(
            course_id=course.id,
            user_id=creator_user.id,
            role=CourseMemberRole.PROFESOR
        )
        prof_member.save()

        return course, None

    @classmethod
    def join_course(cls, code, user):
        course = Course.query.filter_by(course_code=code).first()
        if not course:
            return None, 'No se encontró un curso con ese código.'

        existing = CourseMember.query.filter_by(
            course_id=course.id,
            user_id=user.id
        ).first()
        if existing:
            return None, 'Ya pertenecés a este curso.'

        if course.is_full():
            return None, 'El curso está lleno.'

        from app.modules.schools.models import SchoolMember
        school_member = SchoolMember.query.filter_by(
            school_id=course.school_id,
            user_id=user.id
        ).first()
        if not school_member:
            return None, 'No pertenecés a este colegio. Unite primero con el código del colegio.'

        # Admin y profesores del colegio ya tienen acceso a todos sus cursos.
        # No necesitan (ni pueden) unirse con código como alumnos.
        if school_member.role in (SchoolRole.ADMIN, SchoolRole.PROFESOR):
            return None, 'Sos profesor/admin del colegio: ya tenés acceso a todos sus cursos.'

        member = CourseMember(
            course_id=course.id,
            user_id=user.id,
            role=CourseMemberRole.ALUMNO
        )
        member.save()

        return course, None

    @classmethod
    def add_student_by_email(cls, course_id, email):
        from app.modules.auth.models import User
        user = User.query.filter_by(email=email).first()
        if not user:
            return None, 'No se encontró un usuario con ese email.'

        existing = CourseMember.query.filter_by(
            course_id=course_id,
            user_id=user.id
        ).first()
        if existing:
            return None, f'{user.first_name} {user.last_name} ya pertenece al curso.'

        course = Course.query.get_or_404(course_id)
        school_member = SchoolMember.query.filter_by(
            school_id=course.school_id,
            user_id=user.id
        ).first()
        if not school_member:
            return None, f'{user.first_name} {user.last_name} no pertenece al colegio.'

        if course.is_full():
            return None, 'El curso está lleno.'

        member = CourseMember(
            course_id=course_id,
            user_id=user.id,
            role=CourseMemberRole.ALUMNO
        )
        member.save()

        return member, None

    @classmethod
    def remove_student(cls, course_id, user_id):
        member = CourseMember.query.filter_by(
            course_id=course_id,
            user_id=user_id,
            role=CourseMemberRole.ALUMNO
        ).first()
        if not member:
            return False, 'Alumno no encontrado en este curso.'
        member.delete()
        return True, None

    @classmethod
    def get_school_courses(cls, school_id):
        return Course.query.filter_by(school_id=school_id).all()

    @classmethod
    def get_user_courses_in_school(cls, school_id, user):
        from app.modules.schools.models import SchoolMember
        member = SchoolMember.query.filter_by(
            school_id=school_id,
            user_id=user.id
        ).first()
        if not member:
            return []

        if member.role in (SchoolRole.ADMIN, SchoolRole.PROFESOR):
            return Course.query.filter_by(school_id=school_id).all()

        memberships = CourseMember.query.join(Course).filter(
            Course.school_id == school_id,
            CourseMember.user_id == user.id
        ).all()
        return [m.course for m in memberships]
