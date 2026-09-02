# app/modules/courses/routes.py
"""
Rutas del módulo de cursos.

Cursos pertenecen a un colegio. Los profesores del colegio gestionan,
los alumnos se unen con código.
"""
from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from . import courses_bp
from .forms import CourseForm, JoinCourseForm, AddStudentForm
from .services import CourseService
from .models import Course, CourseMember, CourseMemberRole
from app.modules.schools.models import School, SchoolMember, SchoolRole


# ──────────────────────────────────────────────
#  LISTAR mis cursos (en un colegio)
# ──────────────────────────────────────────────

@courses_bp.route('/')
@login_required
def index():
    memberships = SchoolMember.query.filter_by(user_id=current_user.id).all()
    if not memberships:
        flash('Primero unite a un colegio.', 'info')
        return redirect(url_for('schools.index'))

    if len(memberships) == 1:
        school = memberships[0].school
        return redirect(url_for('courses.list_in_school', school_id=school.id))

    return render_template('courses/select_school.html',
                           memberships=memberships)


# ──────────────────────────────────────────────
#  CURSOS DE UN COLEGIO
# ──────────────────────────────────────────────

@courses_bp.route('/school/<int:school_id>')
@login_required
def list_in_school(school_id):
    school = School.query.get_or_404(school_id)
    school_member = SchoolMember.query.filter_by(
        school_id=school_id,
        user_id=current_user.id
    ).first()
    if not school_member:
        abort(403)

    courses = CourseService.get_user_courses_in_school(school_id, current_user)

    return render_template('courses/index.html',
                           school=school,
                           school_member=school_member,
                           courses=courses)


# ──────────────────────────────────────────────
#  UNIRSE A CURSO CON CÓDIGO
# ──────────────────────────────────────────────

@courses_bp.route('/join', methods=['GET', 'POST'])
@login_required
def join():
    form = JoinCourseForm()
    if form.validate_on_submit():
        course, error = CourseService.join_course(
            code=form.code.data.strip().upper(),
            user=current_user
        )
        if error:
            flash(error, 'danger')
        else:
            flash(f'Te uniste a "{course.title}".', 'success')
            return redirect(url_for('courses.detail', course_id=course.id))
    return render_template('courses/join.html', form=form)


# ──────────────────────────────────────────────
#  CREAR CURSO (profesor/admin en el colegio)
# ──────────────────────────────────────────────

@courses_bp.route('/school/<int:school_id>/new', methods=['GET', 'POST'])
@login_required
def create_in_school(school_id):
    school = School.query.get_or_404(school_id)
    school_member = SchoolMember.query.filter_by(
        school_id=school_id,
        user_id=current_user.id
    ).first()
    if not school_member or school_member.role not in (SchoolRole.ADMIN, SchoolRole.PROFESOR):
        abort(403)

    form = CourseForm()
    if form.validate_on_submit():
        course, error = CourseService.create_course(
            school_id=school_id,
            title=form.title.data,
            description=form.description.data,
            capacity=form.capacity.data,
            creator_user=current_user
        )
        if error:
            flash(error, 'danger')
        else:
            flash(f'Curso creado. Código del curso: {course.course_code}', 'success')
            return redirect(url_for('courses.detail', course_id=course.id))

    return render_template('courses/create.html', form=form, school=school)


# ──────────────────────────────────────────────
#  VER DETALLE DE UN CURSO
# ──────────────────────────────────────────────

@courses_bp.route('/<int:course_id>')
@login_required
def detail(course_id):
    course = Course.query.get_or_404(course_id)

    school_member = SchoolMember.query.filter_by(
        school_id=course.school_id,
        user_id=current_user.id
    ).first()
    if not school_member:
        abort(403)

    # Admin y profesores del colegio acceden a todos sus cursos.
    # Un alumno solo puede ver los cursos donde está inscripto.
    if school_member.role == SchoolRole.ALUMNO:
        if not course.is_member(current_user) or not course.is_alumno(current_user):
            flash('No pertenecés a este curso. Unite con el código del curso.', 'warning')
            return redirect(url_for('courses.join'))

    course_member = course.get_member(current_user)

    return render_template('courses/detail.html',
                           course=course,
                           school=course.school,
                           school_member=school_member,
                           course_member=course_member)

# ──────────────────────────────────────────────
#  EDITAR CURSO (profesor/admin en el colegio)
# ──────────────────────────────────────────────

@courses_bp.route('/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(course_id):
    course = Course.query.get_or_404(course_id)

    school_member = SchoolMember.query.filter_by(
        school_id=course.school_id,
        user_id=current_user.id
    ).first()
    if not school_member or school_member.role not in (SchoolRole.ADMIN, SchoolRole.PROFESOR):
        abort(403)

    form = CourseForm(obj=course)
    if form.validate_on_submit():
        course.title = form.title.data
        course.description = form.description.data or None
        course.capacity = form.capacity.data if form.capacity.data else None
        from app.extensions import db
        db.session.commit()
        flash('Curso actualizado.', 'success')
        return redirect(url_for('courses.detail', course_id=course_id))

    return render_template('courses/edit.html', form=form, course=course, school=course.school)


# ──────────────────────────────────────────────
#  ELIMINAR CURSO (profesor/admin en el colegio)
# ──────────────────────────────────────────────

@courses_bp.route('/<int:course_id>/delete', methods=['POST'])
@login_required
def delete(course_id):
    course = Course.query.get_or_404(course_id)

    school_member = SchoolMember.query.filter_by(
        school_id=course.school_id,
        user_id=current_user.id
    ).first()
    if not school_member or school_member.role not in (SchoolRole.ADMIN, SchoolRole.PROFESOR):
        abort(403)

    school_id = course.school_id
    course.delete()
    flash('Curso eliminado.', 'danger')
    return redirect(url_for('courses.list_in_school', school_id=school_id))


# ──────────────────────────────────────────────
#  VER ALUMNOS (profesor/admin en el colegio)
# ──────────────────────────────────────────────

@courses_bp.route('/<int:course_id>/students')
@login_required
def students(course_id):
    course = Course.query.get_or_404(course_id)

    school_member = SchoolMember.query.filter_by(
        school_id=course.school_id,
        user_id=current_user.id
    ).first()
    if not school_member or school_member.role not in (SchoolRole.ADMIN, SchoolRole.PROFESOR):
        abort(403)

    from sqlalchemy.orm import joinedload
    members = (
        CourseMember.query
        .filter_by(course_id=course_id, role=CourseMemberRole.ALUMNO)
        .options(joinedload(CourseMember.user))
        .all()
    )

    form = AddStudentForm()
    return render_template('courses/students.html',
                           course=course,
                           members=members,
                           form=form,
                           school=course.school)


# ──────────────────────────────────────────────
#  AGREGAR ALUMNO POR EMAIL
# ──────────────────────────────────────────────

@courses_bp.route('/<int:course_id>/students/add', methods=['POST'])
@login_required
def add_student(course_id):
    course = Course.query.get_or_404(course_id)

    school_member = SchoolMember.query.filter_by(
        school_id=course.school_id,
        user_id=current_user.id
    ).first()
    if not school_member or school_member.role not in (SchoolRole.ADMIN, SchoolRole.PROFESOR):
        abort(403)

    form = AddStudentForm()
    if form.validate_on_submit():
        member, error = CourseService.add_student_by_email(
            course_id=course_id,
            email=form.email.data.strip().lower()
        )
        if error:
            flash(error, 'danger')
        else:
            flash(f'{member.user.first_name} {member.user.last_name} fue inscripto.', 'success')

    return redirect(url_for('courses.students', course_id=course_id))


# ──────────────────────────────────────────────
#  QUITAR ALUMNO
# ──────────────────────────────────────────────

@courses_bp.route('/<int:course_id>/students/<int:user_id>/remove', methods=['POST'])
@login_required
def remove_student(course_id, user_id):
    course = Course.query.get_or_404(course_id)

    school_member = SchoolMember.query.filter_by(
        school_id=course.school_id,
        user_id=current_user.id
    ).first()
    if not school_member or school_member.role not in (SchoolRole.ADMIN, SchoolRole.PROFESOR):
        abort(403)

    ok, error = CourseService.remove_student(course_id, user_id)
    if error:
        flash(error, 'info')
    else:
        flash('Alumno removido del curso.', 'info')

    return redirect(url_for('courses.students', course_id=course_id))
