# app/modules/content/routes.py
"""
Rutas del módulo de contenidos.

Permite a los profesores subir materiales (archivos o enlaces)
a sus cursos, y a los alumnos inscriptos verlos/descargarlos.

Reglas de permisos:
  - Profesor dueño del curso → puede subir y eliminar materiales.
  - Alumno inscripto → puede ver y descargar materiales.
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


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────

def _get_course_or_404(course_id):
    """Busca el curso por ID. Si no existe, aborta 404."""
    course = Course.query.get_or_404(course_id)
    return course


def _require_profesor_of(course):
    """
    Verifica que el usuario actual sea profesor y dueño del curso.
    Si no, aborta 403.
    """
    if not current_user.is_authenticated or not current_user.is_profesor():
        abort(403)
    if course.instructor_id != current_user.id:
        abort(403)


def _require_enrolled_or_profesor(course):
    """
    Verifica que el usuario esté inscripto en el curso o sea el profesor dueño.
    Los profesores de otros cursos no pueden ver contenidos de este curso.
    """
    if current_user.is_profesor() and course.instructor_id == current_user.id:
        return  # Es el profesor dueño, acceso permitido
    if current_user.is_alumno() and course.is_enrolled(current_user):
        return  # Está inscripto, acceso permitido
    abort(403)


def _allowed_file(filename):
    """Verifica que la extensión del archivo esté en la lista de permitidas."""
    allowed = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx',
               'mp4', 'avi', 'mov', 'zip', 'rar', 'txt', 'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


# ──────────────────────────────────────────────
#  LISTAR materiales de un curso
# ──────────────────────────────────────────────

@content_bp.route('/course/<int:course_id>')
@login_required
def list_materials(course_id):
    """
    Muestra todos los materiales de un curso.
    - El profesor dueño ve todos los materiales con opciones de eliminar.
    - El alumno inscripto ve los materiales con opción de descargar.
    """
    course = _get_course_or_404(course_id)
    _require_enrolled_or_profesor(course)

    # Traemos los materiales ordenados por fecha de creación (más recientes primero)
    materials = Material.query.filter_by(course_id=course_id).order_by(Material.created_at.desc()).all()

    return render_template('content/list.html',
                           course=course,
                           materials=materials)


# ──────────────────────────────────────────────
#  SUBIR material (solo profesor dueño)
# ──────────────────────────────────────────────

@content_bp.route('/course/<int:course_id>/upload', methods=['GET', 'POST'])
@login_required
def upload(course_id):
    """
    Formulario para subir un material a un curso.
    Solo el profesor dueño puede acceder.

    Flujo de subida de archivo:
      1. Se valida el form (título, tipo, archivo o URL).
      2. Si es archivo:
         a. Se genera un nombre único para evitar colisiones (uuid + extensión).
         b. Se crea la carpeta del curso dentro de uploads/ si no existe.
         c. Se guarda el archivo con werkzeug.utils.save().
      3. Si es enlace:
         a. Se guarda la URL directamente en external_url.
      4. Se crea el registro Material en la base de datos.
    """
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
            # Solo procesamos si se seleccionó un archivo
            if form.file.data:
                file = form.file.data
                filename = secure_filename(file.filename)

                # Generamos nombre único: uuid_original.ext
                # Esto evita que dos archivos con el mismo nombre se pisen.
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                unique_name = f'{uuid.uuid4().hex[:8]}_{filename}'

                # Carpeta específica de este curso dentro de uploads/
                course_folder = os.path.join(
                    current_app.config['UPLOAD_FOLDER'],
                    str(course_id)
                )
                os.makedirs(course_folder, exist_ok=True)

                # Guardamos el archivo
                file.save(os.path.join(course_folder, unique_name))

                # Guardamos la ruta relativa (course_id/nombre_archivo)
                material.file_path = f'{course_id}/{unique_name}'
            else:
                flash('Seleccioná un archivo para subir.', 'danger')
                return render_template('content/upload.html', form=form, course=course)

        elif form.material_type.data == 'link':
            material.external_url = form.external_url.data

        db.session.add(material)
        db.session.commit()

        flash('Material subido con éxito.', 'success')
        return redirect(url_for('content.list_materials', course_id=course_id))

    return render_template('content/upload.html', form=form, course=course)


# ──────────────────────────────────────────────
#  DESCARGAR archivo
# ──────────────────────────────────────────────

@content_bp.route('/download/<int:material_id>')
@login_required
def download(material_id):
    """
    Descarga el archivo asociado a un material.
    Solo funciona para materiales de tipo 'file'.
    El usuario debe estar inscripto en el curso o ser el profesor dueño.

    send_from_directory() es seguro: solo sirve archivos dentro de la
    carpeta especificada, evitando path traversal attacks.
    """
    material = Material.query.get_or_404(material_id)
    course = _get_course_or_404(material.course_id)
    _require_enrolled_or_profesor(course)

    if material.material_type != 'file' or not material.file_path:
        flash('Este material no tiene archivo para descargar.', 'info')
        return redirect(url_for('content.list_materials', course_id=material.course_id))

    # UPLOAD_FOLDER es la carpeta base, file_path es "curso_id/archivo.ext"
    upload_dir = current_app.config['UPLOAD_FOLDER']
    filename = os.path.basename(material.file_path)

    return send_from_directory(
        os.path.join(upload_dir, str(material.course_id)),
        filename,
        as_attachment=True
    )


# ──────────────────────────────────────────────
#  ELIMINAR material (solo profesor dueño)
# ──────────────────────────────────────────────

@content_bp.route('/delete/<int:material_id>', methods=['POST'])
@login_required
def delete(material_id):
    """
    Elimina un material y su archivo asociado (si es tipo 'file').
    Solo el profesor dueño del curso puede eliminar materiales.
    """
    material = Material.query.get_or_404(material_id)
    course = _get_course_or_404(material.course_id)
    _require_profesor_of(course)

    # Si tiene archivo físico, lo borramos del disco también
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
