# app/modules/courses/routes.py
"""
Rutas del módulo de cursos.

Cada ruta es un endpoint que Flask asocia a una URL.
Se usa @login_required de Flask-Login para exigir sesión activa.
El chequeo de rol (profesor vs alumno) se hace con la función
 auxiliar _require_profesor() que definimos abajo.

Patrón usado en cada ruta:
  1. Si es POST: recibir y validar el form → actuar → redirigir
  2. Si es GET: mostrar el form o los datos → renderizar template
"""
from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from . import courses_bp
from .forms import CourseForm, AddStudentForm
from .services import CourseService
from .models import Course, Enrollment
from app.extensions import db
from app.modules.auth.models import User


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────

def _require_profesor():
    """
    Chequea que el usuario logueado sea profesor.
    Si no lo es, aborta con 403 (Forbidden).

    ¿Por qué abort() y no redirect?
    Porque si un alumno intenta acceder a una ruta de profesor,
    no queremos mandarlo al login — queremos que vea que no tiene permiso.
    """
    if not current_user.is_authenticated or not current_user.is_profesor():
        abort(403)


# ──────────────────────────────────────────────
#  LISTAR cursos (cualquier usuario logueado)
# ──────────────────────────────────────────────

@courses_bp.route('/')
@login_required
def index():
    """
    Muestra la lista de todos los cursos disponibles.
    - Profesores ven todos los cursos (pueden filtrar por los suyos en el template).
    - Alumnos ven todos los cursos y pueden inscribirse.

    CourseService.get_all() usa el BaseModel.query.all() que ya está implementado.
    """
    courses = CourseService.get_all()
    return render_template('courses/index.html', courses=courses)


# ──────────────────────────────────────────────
#  CREAR curso (solo profesores)
# ──────────────────────────────────────────────

@courses_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    """
    Formulario para crear un nuevo curso.
    Solo profesores pueden acceder.

    Al enviar el form (POST):
      1. Se valida con CourseForm (WTForms se encarga de los validators)
      2. Se crea el curso con instructor_id = current_user.id
      3. Se redirige al listado de cursos

    Al acceder por GET:
      Se muestra el form vacío para que el profesor lo complete.
    """
    _require_profesor()

    form = CourseForm()

    if form.validate_on_submit():
        # create() viene del BaseService: crea una instancia del modelo,
        # le pone los kwargs, hace db.session.add + commit
        CourseService.create(
            title=form.title.data,
            description=form.description.data or None,
            capacity=form.capacity.data,
            instructor_id=current_user.id
        )
        flash('Curso creado con éxito.', 'success')
        return redirect(url_for('courses.index'))

    return render_template('courses/create.html', form=form)


# ──────────────────────────────────────────────
#  VER detalle de un curso (cualquier usuario logueado)
# ──────────────────────────────────────────────

@courses_bp.route('/<int:course_id>')
@login_required
def detail(course_id):
    """
    Muestra el detalle de un curso: título, descripción, profesor,
    cantidad de inscriptos, y si el alumno actual está inscripto.

    get_by_id() viene del BaseService: hace Course.query.get_or_404(id),
    si no existe devuelve automáticamente un 404.
    """
    course = CourseService.get_by_id(course_id)
    return render_template('courses/detail.html', course=course)


# ──────────────────────────────────────────────
#  EDITAR curso (solo el profesor que lo creó)
# ──────────────────────────────────────────────

@courses_bp.route('/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(course_id):
    """
    Formulario para editar un curso existente.
    Solo el profesor que creó el curso puede editarlo.

    En GET: se precargan los campos del form con obj=course (WTForms lo hace solo).
    En POST: se validan los datos y se actualiza cada campo con setattr.
    """
    _require_profesor()

    course = CourseService.get_by_id(course_id)

    # Solo el dueño del curso puede editarlo
    if course.instructor_id != current_user.id:
        abort(403)

    form = CourseForm(obj=course)

    if form.validate_on_submit():
        CourseService.update(
            id=course_id,
            title=form.title.data,
            description=form.description.data or None,
            capacity=form.capacity.data
        )
        flash('Curso actualizado.', 'success')
        return redirect(url_for('courses.detail', course_id=course_id))

    return render_template('courses/edit.html', form=form, course=course)


# ──────────────────────────────────────────────
#  ELIMINAR curso (solo el profesor que lo creó)
# ──────────────────────────────────────────────

@courses_bp.route('/<int:course_id>/delete', methods=['POST'])
@login_required
def delete(course_id):
    """
    Elimina un curso y todas sus inscripciones (cascade).
    Solo el profesor dueño puede eliminarlo.

    ¿Por qué solo POST y no GET?
    Porque eliminar es una acción destructiva. En GET se confía en
    que el browser o un link no accidental la ejecute.
    Con POST se exige que el usuario envíe un form explícitamente.
    """
    _require_profesor()

    course = CourseService.get_by_id(course_id)

    if course.instructor_id != current_user.id:
        abort(403)

    CourseService.delete(course_id)
    flash('Curso eliminado.', 'danger')
    return redirect(url_for('courses.index'))


# ──────────────────────────────────────────────
#  INSCRIBIRSE a un curso (solo alumnos)
# ──────────────────────────────────────────────

@courses_bp.route('/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll(course_id):
    """
    Inscribe al alumno logueado en un curso.
    Validaciones:
      - Debe ser alumno (un profesor no se inscribe).
      - No puede inscribirse dos veces al mismo curso (UniqueConstraint).
      - El curso no debe estar lleno (si tiene capacidad definida).
    """
    # Solo alumnos se inscriben
    if not current_user.is_alumno():
        flash('Solo los alumnos pueden inscribirse a cursos.', 'danger')
        return redirect(url_for('courses.detail', course_id=course_id))

    course = CourseService.get_by_id(course_id)

    # Verificar si ya está inscripto
    if course.is_enrolled(current_user):
        flash('Ya estás inscripto en este curso.', 'info')
        return redirect(url_for('courses.detail', course_id=course_id))

    # Verificar capacidad
    if course.is_full():
        flash('Este curso está lleno.', 'warning')
        return redirect(url_for('courses.detail', course_id=course_id))

    # Crear la inscripción
    enrollment = Enrollment(
        course_id=course_id,
        student_id=current_user.id
    )
    db.session.add(enrollment)
    db.session.commit()

    flash(f'Te inscribiste en "{course.title}".', 'success')
    return redirect(url_for('courses.detail', course_id=course_id))


# ──────────────────────────────────────────────
#  DESINSCRIBIRSE de un curso (solo alumnos)
# ──────────────────────────────────────────────

@courses_bp.route('/<int:course_id>/unenroll', methods=['POST'])
@login_required
def unenroll(course_id):
    """
    Quita la inscripción del alumno logueado de un curso.
    El alumno solo puede desinscribirse de cursos donde está inscripto.
    """
    if not current_user.is_alumno():
        flash('Acción no válida.', 'danger')
        return redirect(url_for('courses.detail', course_id=course_id))

    enrollment = Enrollment.query.filter_by(
        course_id=course_id,
        student_id=current_user.id
    ).first()

    if not enrollment:
        flash('No estás inscripto en este curso.', 'info')
        return redirect(url_for('courses.detail', course_id=course_id))

    db.session.delete(enrollment)
    db.session.commit()

    flash('Te desinscribiste del curso.', 'info')
    return redirect(url_for('courses.detail', course_id=course_id))


# ──────────────────────────────────────────────
#  MIS CURSOS (se adapta según el rol)
# ──────────────────────────────────────────────

@courses_bp.route('/my')
@login_required
def my_courses():
    """
    Vista "Mis cursos" — se comporta distinto según el rol:

    PROFESOR: muestra los cursos que él creó, con la cantidad
    de alumnos inscriptos en cada uno. Desde ahí puede entrar
    a gestionar los alumnos de cada curso.

    ALUMNO: muestra los cursos en los que está inscripto,
    con la posibilidad de desinscribirse.
    """
    if current_user.is_profesor():
        # Filtramos solo los cursos donde instructor_id = usuario actual.
        # Usamos filter() en vez de get_all() porque necesitamos filtrar.
        courses = Course.query.filter_by(instructor_id=current_user.id).all()
        return render_template('courses/my_profesor.html', courses=courses)
    else:
        # Para alumnos: buscamos todas sus inscripciones y de ahí sacamos los cursos.
        # enrollment.course sigue la FK y devuelve el objeto Course.
        enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
        courses = [e.course for e in enrollments]
        return render_template('courses/my_alumno.html', courses=courses)


# ──────────────────────────────────────────────
#  VER ALUMNOS de un curso (solo el profesor dueño)
# ──────────────────────────────────────────────

@courses_bp.route('/<int:course_id>/students')
@login_required
def students(course_id):
    """
    Lista todos los alumnos inscriptos en un curso.
    Solo el profesor que creó el curso puede ver esta vista.

    Para cada alumno mostramos: nombre, apellido, email, y la fecha
    en que se inscribió (created_at del enrollment).
    """
    _require_profesor()

    course = CourseService.get_by_id(course_id)

    if course.instructor_id != current_user.id:
        abort(403)

    # Traemos los enrollments con el alumno incluido (eager loading con join).
    # Si usáramos course.enrollments, cada acceso al alumno haría una query
    # distinta (N+1 problem). Con .options(joinedload) SQLAlchemy trae todo
    # en una sola query usando un JOIN.
    from sqlalchemy.orm import joinedload
    enrollments = (
        Enrollment.query
        .filter_by(course_id=course_id)
        .options(joinedload(Enrollment.student))
        .all()
    )

    form = AddStudentForm()
    return render_template('courses/students.html',
                           course=course,
                           enrollments=enrollments,
                           form=form)


# ──────────────────────────────────────────────
#  AGREGAR ALUMNO al curso (solo el profesor dueño)
# ──────────────────────────────────────────────

@courses_bp.route('/<int:course_id>/students/add', methods=['POST'])
@login_required
def add_student(course_id):
    """
    Ruta POST que recibe el email de un alumno y lo inscribe al curso.

    Flujo:
      1. Se busca el usuario por email en la tabla users.
      2. Se verifica que exista y que sea alumno (no profesor).
      3. Se verifica que no esté ya inscripto.
      4. Se verifica la capacidad del curso.
      5. Se crea la inscripción.

    Si algo falla, se muestra un flash con el error y se redirige
    de vuelta a la lista de alumnos.
    """
    _require_profesor()

    course = CourseService.get_by_id(course_id)

    if course.instructor_id != current_user.id:
        abort(403)

    form = AddStudentForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        # Buscar el usuario por email
        student = User.query.filter_by(email=email).first()

        if not student:
            flash(f'No se encontró ningún usuario con el email "{email}".', 'danger')
            return redirect(url_for('courses.students', course_id=course_id))

        if not student.is_alumno():
            flash('Ese email pertenece a un profesor, no se puede inscribir.', 'danger')
            return redirect(url_for('courses.students', course_id=course_id))

        # Verificar si ya está inscripto
        existing = Enrollment.query.filter_by(
            course_id=course_id,
            student_id=student.id
        ).first()

        if existing:
            flash(f'{student.first_name} {student.last_name} ya está inscripto.', 'info')
            return redirect(url_for('courses.students', course_id=course_id))

        # Verificar capacidad
        if course.is_full():
            flash('El curso está lleno. No se puede agregar más alumnos.', 'warning')
            return redirect(url_for('courses.students', course_id=course_id))

        # Crear la inscripción
        enrollment = Enrollment(
            course_id=course_id,
            student_id=student.id
        )
        db.session.add(enrollment)
        db.session.commit()

        flash(f'{student.first_name} {student.last_name} fue inscripto.', 'success')

    return redirect(url_for('courses.students', course_id=course_id))


# ──────────────────────────────────────────────
#  QUITAR ALUMNO del curso (solo el profesor dueño)
# ──────────────────────────────────────────────

@courses_bp.route('/<int:course_id>/students/<int:student_id>/remove', methods=['POST'])
@login_required
def remove_student(course_id, student_id):
    """
    Elimina la inscripción de un alumno de un curso.

    El profesorDueño puede quitar alumnos de su curso.
    Se busca la inscripción por course_id + student_id y se elimina.
    """
    _require_profesor()

    course = CourseService.get_by_id(course_id)

    if course.instructor_id != current_user.id:
        abort(403)

    enrollment = Enrollment.query.filter_by(
        course_id=course_id,
        student_id=student_id
    ).first()

    if not enrollment:
        flash('Ese alumno no está inscripto en este curso.', 'info')
        return redirect(url_for('courses.students', course_id=course_id))

    student_name = f'{enrollment.student.first_name} {enrollment.student.last_name}'

    db.session.delete(enrollment)
    db.session.commit()

    flash(f'{student_name} fue removido del curso.', 'info')
    return redirect(url_for('courses.students', course_id=course_id))
