# app/modules/evaluations/routes.py
"""
Rutas del módulo de evaluaciones.

Flujo del profesor:
  1. Crea un examen (título, descripción, tiempo).
  2. Agrega preguntas de opción múltiple una por una.
  3. Puede ver las notas de sus alumnos.

Flujo del alumno:
  1. Ve los exámenes disponibles de un curso.
  2. Si no rindió, puede iniciar el examen.
  3. Responde las preguntas y envía.
  4. Se califica automáticamente y ve su nota.

La calificación es automática: se comparan las respuestas del alumno
con las respuestas correctas y se calcula el porcentaje.
"""
from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from . import evaluations_bp
from .forms import ExamForm, QuestionForm
from .services import EvaluationService
from .models import Exam, Question, StudentAnswer, Grade
from app.extensions import db
from app.modules.courses.models import Course, Enrollment


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────

def _get_course_or_404(course_id):
    """Busca el curso por ID. Si no existe, aborta 404."""
    return Course.query.get_or_404(course_id)


def _require_profesor_of(course):
    """Verifica que el usuario sea profesor dueño del curso."""
    if not current_user.is_authenticated or not current_user.is_profesor():
        abort(403)
    if course.instructor_id != current_user.id:
        abort(403)


def _require_enrolled(course):
    """Verifica que el alumno esté inscripto en el curso."""
    if not current_user.is_alumno():
        abort(403)
    if not course.is_enrolled(current_user):
        abort(403)


# ──────────────────────────────────────────────
#  LISTAR exámenes de un curso
# ──────────────────────────────────────────────

@evaluations_bp.route('/course/<int:course_id>')
@login_required
def list_exams(course_id):
    """
    Muestra todos los exámenes de un curso.

    - El profesor ve los exámenes con la cantidad de alumnos que rindieron.
    - El alumno ve los exámenes con su nota si ya rindió, o el botón para rendir.
    """
    course = _get_course_or_404(course_id)

    # Verificar permisos: profesor dueño O alumno inscripto
    if current_user.is_profesor():
        if course.instructor_id != current_user.id:
            abort(403)
    elif current_user.is_alumno():
        _require_enrolled(course)
    else:
        abort(403)

    exams = Exam.query.filter_by(course_id=course_id).order_by(Exam.created_at.desc()).all()

    return render_template('evaluations/list.html',
                           course=course,
                           exams=exams)


# ──────────────────────────────────────────────
#  CREAR examen (solo profesor dueño)
# ──────────────────────────────────────────────

@evaluations_bp.route('/course/<int:course_id>/new', methods=['GET', 'POST'])
@login_required
def create_exam(course_id):
    """
    Formulario para crear un examen.
    Solo el profesor dueño del curso puede crear exámenes.

    Después de crear el examen, se redirige a agregar preguntas.
    """
    course = _get_course_or_404(course_id)
    _require_profesor_of(course)

    form = ExamForm()

    if form.validate_on_submit():
        exam = Exam(
            course_id=course_id,
            title=form.title.data,
            description=form.description.data or None,
            time_limit=form.time_limit.data
        )
        db.session.add(exam)
        db.session.commit()

        flash('Examen creado. Ahora agregá las preguntas.', 'success')
        return redirect(url_for('evaluations.add_question', exam_id=exam.id))

    return render_template('evaluations/create_exam.html', form=form, course=course)


# ──────────────────────────────────────────────
#  AGREGAR PREGUNTA a un examen (solo profesor dueño)
# ──────────────────────────────────────────────

@evaluations_bp.route('/exam/<int:exam_id>/add-question', methods=['GET', 'POST'])
@login_required
def add_question(exam_id):
    """
    Formulario para agregar una pregunta a un examen.

    El profesor puede agregar las preguntas una por una.
    Después de cada pregunta, se muestra el form de nuevo para agregar otra.
    Cuando termine, puede ir a ver el examen completo.
    """
    exam = Exam.query.get_or_404(exam_id)
    course = _get_course_or_404(exam.course_id)
    _require_profesor_of(course)

    form = QuestionForm()

    if form.validate_on_submit():
        question = Question(
            exam_id=exam_id,
            text=form.text.data,
            option_a=form.option_a.data,
            option_b=form.option_b.data,
            option_c=form.option_c.data,
            option_d=form.option_d.data,
            correct_option=form.correct_option.data
        )
        db.session.add(question)
        db.session.commit()

        flash(f'Pregunta #{exam.total_questions()} agregada.', 'success')
        # Redirige de vuelta al form para agregar otra pregunta
        return redirect(url_for('evaluations.add_question', exam_id=exam_id))

    return render_template('evaluations/add_question.html',
                           form=form,
                           exam=exam,
                           course=course,
                           question_count=exam.total_questions())


# ──────────────────────────────────────────────
#  RENDIR examen (solo alumnos inscriptos)
# ──────────────────────────────────────────────

@evaluations_bp.route('/exam/<int:exam_id>/take')
@login_required
def take_exam(exam_id):
    """
    Muestra el examen para que el alumno lo responda.

    Validaciones:
      - Debe ser alumno.
      - Debe estar inscripto en el curso.
      - No puede rendir dos veces el mismo examen.
      - El examen debe tener al menos una pregunta.
    """
    exam = Exam.query.get_or_404(exam_id)
    course = _get_course_or_404(exam.course_id)

    # Verificar que sea alumno inscripto
    if not current_user.is_alumno():
        flash('Solo los alumnos pueden rendir exámenes.', 'danger')
        return redirect(url_for('evaluations.list_exams', course_id=exam.course_id))

    _require_enrolled(course)

    # Verificar que no haya rendido ya
    if exam.has_been_taken_by(current_user):
        flash('Ya rendiste este examen.', 'info')
        return redirect(url_for('evaluations.view_result', exam_id=exam_id))

    # Verificar que tenga preguntas
    if exam.total_questions() == 0:
        flash('Este examen todavía no tiene preguntas.', 'warning')
        return redirect(url_for('evaluations.list_exams', course_id=exam.course_id))

    # Traemos las preguntas para mostrarlas
    questions = exam.questions

    return render_template('evaluations/take_exam.html',
                           exam=exam,
                           course=course,
                           questions=questions)


# ──────────────────────────────────────────────
#  ENVIAR respuestas del examen (POST)
# ──────────────────────────────────────────────

@evaluations_bp.route('/exam/<int:exam_id>/submit', methods=['POST'])
@login_required
def submit_exam(exam_id):
    """
    Recibe las respuestas del alumno, las califica y crea el Grade.

    Flujo:
      1. Se obtienen todas las respuestas del form (question_X = 'a','b','c','d').
      2. Para cada pregunta, se crea un StudentAnswer.
      3. Se comparan las respuestas con las correctas.
      4. Se calcula el score (correctas / total).
      5. Se crea el Grade con el porcentaje.
      6. Se redirige al resultado.
    """
    exam = Exam.query.get_or_404(exam_id)
    course = _get_course_or_404(exam.course_id)

    if not current_user.is_alumno() or not course.is_enrolled(current_user):
        abort(403)

    if exam.has_been_taken_by(current_user):
        flash('Ya rendiste este examen.', 'info')
        return redirect(url_for('evaluations.view_result', exam_id=exam_id))

    questions = exam.questions
    score = 0

    for question in questions:
        # El nombre del campo en el form es "question_{id}"
        chosen = request.form.get(f'question_{question.id}')

        if chosen in ('a', 'b', 'c', 'd'):
            # Guardamos la respuesta del alumno
            answer = StudentAnswer(
                question_id=question.id,
                student_id=current_user.id,
                chosen_option=chosen
            )
            db.session.add(answer)

            # Checkeamos si es correcta
            if chosen == question.correct_option:
                score += 1

    # Creamos la calificación
    total = len(questions)
    grade = Grade(
        exam_id=exam_id,
        student_id=current_user.id,
        score=score,
        total=total
    )
    db.session.add(grade)
    db.session.commit()

    flash(f'Examen enviado. Tu nota: {score}/{total} ({grade.percentage()}%)', 'success')
    return redirect(url_for('evaluations.view_result', exam_id=exam_id))


# ──────────────────────────────────────────────
#  VER RESULTADO de un examen
# ──────────────────────────────────────────────

@evaluations_bp.route('/exam/<int:exam_id>/result')
@login_required
def view_result(exam_id):
    """
    Muestra el resultado del examen para el alumno:
      - Nota final (score/total y porcentaje).
      - Lista de preguntas con la respuesta del alumno y la correcta.
      - Indica cuáles acertó y cuáles falló.
    """
    exam = Exam.query.get_or_404(exam_id)
    course = _get_course_or_404(exam.course_id)

    grade = exam.get_grade_for(current_user)
    if not grade:
        flash('Todavía no rendiste este examen.', 'info')
        return redirect(url_for('evaluations.list_exams', course_id=exam.course_id))

    # Traemos las respuestas del alumno para este examen
    # Un dict rápido: question_id → StudentAnswer
    answers = {}
    for q in exam.questions:
        sa = StudentAnswer.query.filter_by(
            question_id=q.id,
            student_id=current_user.id
        ).first()
        if sa:
            answers[q.id] = sa

    return render_template('evaluations/view_result.html',
                           exam=exam,
                           course=course,
                           grade=grade,
                           answers=answers)


# ──────────────────────────────────────────────
#  VER NOTAS de un examen (solo profesor dueño)
# ──────────────────────────────────────────────

@evaluations_bp.route('/exam/<int:exam_id>/grades')
@login_required
def view_grades(exam_id):
    """
    Muestra todas las calificaciones de un examen.
    Solo el profesor dueño del curso puede ver esta vista.
    """
    exam = Exam.query.get_or_404(exam_id)
    course = _get_course_or_404(exam.course_id)
    _require_profesor_of(course)

    grades = Grade.query.filter_by(exam_id=exam_id).order_by(Grade.created_at.desc()).all()

    return render_template('evaluations/view_grades.html',
                           exam=exam,
                           course=course,
                           grades=grades)


# ──────────────────────────────────────────────
#  ELIMINAR examen (solo profesor dueño)
# ──────────────────────────────────────────────

@evaluations_bp.route('/exam/<int:exam_id>/delete', methods=['POST'])
@login_required
def delete_exam(exam_id):
    """
    Elimina un examen y todas sus preguntas, respuestas y calificaciones (cascade).
    Solo el profesor dueño puede eliminar.
    """
    exam = Exam.query.get_or_404(exam_id)
    course = _get_course_or_404(exam.course_id)
    _require_profesor_of(course)

    course_id = exam.course_id

    db.session.delete(exam)
    db.session.commit()

    flash('Examen eliminado.', 'info')
    return redirect(url_for('evaluations.list_exams', course_id=course_id))
