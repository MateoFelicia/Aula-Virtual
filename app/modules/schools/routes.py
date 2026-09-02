# app/modules/schools/routes.py
"""
Rutas del módulo de colegios.

Flujo:
  1. Crear colegio → el creador queda como admin.
  2. Unirse con código → el usuario queda como alumno.
  3. Admin gestiona miembros (agregar, quitar, promover, degradar).
"""
from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from . import schools_bp
from .forms import CreateSchoolForm, JoinSchoolForm, AddMemberForm
from .services import SchoolService
from .models import School, SchoolMember, SchoolRole


# ──────────────────────────────────────────────
#  LISTAR MIS COLEGIOS
# ──────────────────────────────────────────────

@schools_bp.route('/')
@login_required
def index():
    schools = SchoolService.get_user_schools(current_user)
    return render_template('schools/index.html', schools=schools)


# ──────────────────────────────────────────────
#  CREAR COLEGIO
# ──────────────────────────────────────────────

@schools_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    form = CreateSchoolForm()
    if form.validate_on_submit():
        school = SchoolService.create_school(
            name=form.name.data,
            description=form.description.data,
            admin_user=current_user
        )
        flash(f'Colegio "{school.name}" creado. Tu código: {school.code}', 'success')
        return redirect(url_for('schools.detail', school_id=school.id))
    return render_template('schools/create.html', form=form)


# ──────────────────────────────────────────────
#  UNIRSE A UN COLEGIO
# ──────────────────────────────────────────────

@schools_bp.route('/join', methods=['GET', 'POST'])
@login_required
def join():
    form = JoinSchoolForm()
    if form.validate_on_submit():
        school, error = SchoolService.join_school(
            code=form.code.data.strip().upper(),
            user=current_user
        )
        if error:
            flash(error, 'danger')
        else:
            flash(f'Te uniste a "{school.name}".', 'success')
            return redirect(url_for('schools.detail', school_id=school.id))
    return render_template('schools/join.html', form=form)


# ──────────────────────────────────────────────
#  VER DETALLE DEL COLEGIO
# ──────────────────────────────────────────────

@schools_bp.route('/<int:school_id>')
@login_required
def detail(school_id):
    school = School.query.get_or_404(school_id)
    if not school.is_member(current_user):
        abort(403)

    member = school.get_member(current_user)
    members = SchoolMember.query.filter_by(school_id=school_id).all()

    from app.modules.courses.services import CourseService
    courses = CourseService.get_user_courses_in_school(school_id, current_user)

    return render_template('schools/detail.html',
                           school=school,
                           member=member,
                           members=members,
                           courses=courses)


# ──────────────────────────────────────────────
#  GESTIONAR MIEMBROS (solo admin)
# ──────────────────────────────────────────────

@schools_bp.route('/<int:school_id>/members')
@login_required
def members(school_id):
    school = School.query.get_or_404(school_id)
    if not school.is_member(current_user):
        abort(403)
    if not school.is_admin(current_user):
        abort(403)

    members = SchoolMember.query.filter_by(school_id=school_id).all()
    form = AddMemberForm()
    return render_template('schools/members.html',
                           school=school,
                           members=members,
                           form=form)


@schools_bp.route('/<int:school_id>/members/add', methods=['POST'])
@login_required
def add_member(school_id):
    school = School.query.get_or_404(school_id)
    if not school.is_admin(current_user):
        abort(403)

    form = AddMemberForm()
    if form.validate_on_submit():
        member, error = SchoolService.add_member_by_email(
            school_id=school_id,
            email=form.email.data.strip().lower()
        )
        if error:
            flash(error, 'danger')
        else:
            flash(f'{member.user.first_name} {member.user.last_name} fue agregado como alumno.', 'success')

    return redirect(url_for('schools.members', school_id=school_id))


@schools_bp.route('/<int:school_id>/members/<int:user_id>/promote', methods=['POST'])
@login_required
def promote(school_id, user_id):
    school = School.query.get_or_404(school_id)
    if not school.is_admin(current_user):
        abort(403)

    ok, error = SchoolService.promote_to_profesor(school_id, user_id)
    if error:
        flash(error, 'danger')
    else:
        flash('Miembro promovido a profesor.', 'success')

    return redirect(url_for('schools.members', school_id=school_id))


@schools_bp.route('/<int:school_id>/members/<int:user_id>/demote', methods=['POST'])
@login_required
def demote(school_id, user_id):
    school = School.query.get_or_404(school_id)
    if not school.is_admin(current_user):
        abort(403)

    ok, error = SchoolService.demote_to_alumno(school_id, user_id)
    if error:
        flash(error, 'danger')
    else:
        flash('Miembro degradado a alumno.', 'info')

    return redirect(url_for('schools.members', school_id=school_id))


@schools_bp.route('/<int:school_id>/members/<int:user_id>/remove', methods=['POST'])
@login_required
def remove_member(school_id, user_id):
    school = School.query.get_or_404(school_id)
    if not school.is_admin(current_user):
        abort(403)

    ok, error = SchoolService.remove_member(school_id, user_id)
    if error:
        flash(error, 'danger')
    else:
        flash('Miembro removido del colegio.', 'info')

    return redirect(url_for('schools.members', school_id=school_id))


# ──────────────────────────────────────────────
#  ROTAR CÓDIGO DEL COLEGIO (solo admin)
# ──────────────────────────────────────────────

@schools_bp.route('/<int:school_id>/rotate-code', methods=['POST'])
@login_required
def rotate_code(school_id):
    school = School.query.get_or_404(school_id)
    if not school.is_admin(current_user):
        abort(403)

    new_code = School.generate_code()
    while School.query.filter_by(code=new_code).first():
        new_code = School.generate_code()

    school.code = new_code
    from app.extensions import db
    db.session.commit()

    flash(f'Nuevo código del colegio: {new_code}', 'success')
    return redirect(url_for('schools.detail', school_id=school_id))
