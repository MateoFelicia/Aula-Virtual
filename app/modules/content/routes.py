# app/modules/content/routes.py
"""
Rutas del módulo de contenidos.

Permite a los profesores del colegio subir materiales a un curso,
y a los alumnos inscriptos verlos/descargarlos.

Reglas de permisos:
  - Profesor o admin en el colegio → puede subir y eliminar materiales.
  - Alumno inscripto en el curso → puede ver y descargar materiales.
  - Cualquier otro usuario → no tiene acceso.
"""
import os
import uuid
from flask import render_template, redirect, url_for, flash, abort, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import content_bp
from .forms import MaterialForm
from .services import ContentService
from .models import Material
from app.extensions import db
from app.modules.courses.models import Course
from app.modules.schools.models import SchoolMember, SchoolRole


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────

def _get_course_or_404(course_id):
    return Course.query.get_or_404(course_id)


def _require_profesor_of(course):
    school_member = SchoolMember.query.filter_by(
        school_id=course.school_id,
        user_id=current_user.id
    ).first()
    if not school_member or school_member.role not in (SchoolRole.ADMIN, SchoolRole.PROFESOR):
        abort(403)
    return school_member


def _require_enrolled_or_profesor(course):
    school_member = SchoolMember.query.filter_by(
        school_id=course.school_id,
        user_id=current_user.id
    ).first()
    if not school_member:
        abort(403)

    if school_member.role in (SchoolRole.ADMIN, SchoolRole.PROFESOR):
        return school_member

    if course.is_member(current_user) and course.is_alumno(current_user):
        return school_member

    abort(403)


# ──────────────────────────────────────────────
#  LISTAR materiales de un curso
# ──────────────────────────────────────────────

@content_bp.route('/course/<int:course_id>')
@login_required
def list_materials(course_id):
    course = _get_course_or_404(course_id)
    school_member = _require_enrolled_or_profesor(course)

    materials = Material.query.filter_by(course_id=course_id).order_by(Material.created_at.desc()).all()

    return render_template('content/list.html',
                           course=course,
                           materials=materials,
                           school=course.school,
                           school_member=school_member)


# ──────────────────────────────────────────────
#  SUBIR material (profesor/admin en el colegio)
# ──────────────────────────────────────────────

@content_bp.route('/course/<int:course_id>/upload', methods=['GET', 'POST'])
@login_required
def upload(course_id):
    course = _get_course_or_404(course_id)
    _require_profesor_of(course)

    form = MaterialForm()

    if form.validate_on_submit():
        material = Material(
            course_id=course_id,
            title=form.title.data,
            description=form.description.data or None,
            material_type=form.material_type.data
        )

        if form.material_type.data == 'file':
            if form.file.data:
                file = form.file.data
                filename = secure_filename(file.filename)
                unique_name = f'{uuid.uuid4().hex[:8]}_{filename}'

                course_folder = os.path.join(
                    current_app.config['UPLOAD_FOLDER'],
                    str(course_id)
                )
                os.makedirs(course_folder, exist_ok=True)

                file.save(os.path.join(course_folder, unique_name))

                material.file_path = f'{course_id}/{unique_name}'
            else:
                flash('Seleccioná un archivo para subir.', 'danger')
                return render_template('content/upload.html', form=form, course=course, school=course.school)

        elif form.material_type.data == 'link':
            material.external_url = form.external_url.data

        db.session.add(material)
        db.session.commit()

        flash('Material subido con éxito.', 'success')
        return redirect(url_for('content.list_materials', course_id=course_id))

    return render_template('content/upload.html', form=form, course=course, school=course.school)


# ──────────────────────────────────────────────
#  DESCARGAR archivo
# ──────────────────────────────────────────────

@content_bp.route('/download/<int:material_id>')
@login_required
def download(material_id):
    material = Material.query.get_or_404(material_id)
    course = _get_course_or_404(material.course_id)
    _require_enrolled_or_profesor(course)

    if material.material_type != 'file' or not material.file_path:
        flash('Este material no tiene archivo para descargar.', 'info')
        return redirect(url_for('content.list_materials', course_id=material.course_id))

    upload_dir = current_app.config['UPLOAD_FOLDER']
    filename = os.path.basename(material.file_path)

    return send_from_directory(
        os.path.join(upload_dir, str(material.course_id)),
        filename,
        as_attachment=True
    )


# ──────────────────────────────────────────────
#  ELIMINAR material (profesor/admin en el colegio)
# ──────────────────────────────────────────────

@content_bp.route('/delete/<int:material_id>', methods=['POST'])
@login_required
def delete(material_id):
    material = Material.query.get_or_404(material_id)
    course = _get_course_or_404(material.course_id)
    _require_profesor_of(course)

    if material.file_path:
        file_full_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            material.file_path
        )
        if os.path.exists(file_full_path):
            os.remove(file_full_path)

    db.session.delete(material)
    db.session.commit()

    flash('Material eliminado.', 'info')
    return redirect(url_for('content.list_materials', course_id=material.course_id))
