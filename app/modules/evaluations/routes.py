# app/modules/evaluations/routes.py
"""
Rutas del módulo de evaluaciones.

Flujo del profesor/admin del colegio:
  1. Crea un examen (título, descripción, tiempo).
  2. Agrega preguntas de opción múltiple una por una.
  3. Puede ver las notas de sus alumnos.

Flujo del alumno inscripto:
  1. Ve los exámenes disponibles de un curso.
  2. Si no rindió, puede iniciar el examen.
  3. Responde las preguntas y envía.
  4. Se califica automáticamente y ve su nota.
"""
from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from . import evaluations_bp
from .forms import ExamForm, QuestionForm
from .services import EvaluationService
from .models import Exam, Question, StudentAnswer, Grade
from app.extensions import db
from app.modules.courses.models import Course, CourseMember, CourseMemberRole
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


def _require_enrolled(course):
    if not course.is_member(current_user) or not course.is_alumno(current_user):
        abort(403)


# ──────────────────────────────────────────────
#  LISTAR exámenes de un curso
# ──────────────────────────────────────────────

@evaluations_bp.route('/course/<int:course_id>')
@login_required
def list_exams(course_id):
    course = _get_course_or_404(course_id)

    school_member = SchoolMember.query.filter_by(
        school_id=course.school_id,
        user_id=current_user.id
    ).first()
    if not school_member:
        abort(403)

    if school_member.role in (SchoolRole.ADMIN, SchoolRole.PROFESOR):
        pass
    elif course.is_member(current_user) and course.is_alumno(current_user):
        _require_enrolled(course)
    else:
        abort(403)

    exams = Exam.query.filter_by(course_id=course_id).order_by(Exam.created_at.desc()).all()

    return render_template('evaluations/list.html',
                           course=course,
                           exams=exams,
                           school=course.school,
                           school_member=school_member,
                           course_member=course.get_member(current_user))


# ──────────────────────────────────────────────
#  CREAR examen (profesor/admin en el colegio)
# ──────────────────────────────────────────────

@evaluations_bp.route('/course/<int:course_id>/new', methods=['GET', 'POST'])
@login_required
def create_exam(course_id):
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

    return render_template('evaluations/create_exam.html', form=form, course=course, school=course.school)


# ──────────────────────────────────────────────
#  AGREGAR PREGUNTA (profesor/admin en el colegio)
# ──────────────────────────────────────────────

@evaluations_bp.route('/exam/<int:exam_id>/add-question', methods=['GET', 'POST'])
@login_required
def add_question(exam_id):
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
        return redirect(url_for('evaluations.add_question', exam_id=exam_id))

    return render_template('evaluations/add_question.html',
                           form=form,
                           exam=exam,
                           course=course,
                           school=course.school,
                           question_count=exam.total_questions())


# ──────────────────────────────────────────────
#  RENDIR examen (alumnos inscriptos)
# ──────────────────────────────────────────────

@evaluations_bp.route('/exam/<int:exam_id>/take')
@login_required
def take_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    course = _get_course_or_404(exam.course_id)

    if not course.is_member(current_user) or not course.is_alumno(current_user):
        flash('Solo los alumnos inscriptos pueden rendir exámenes.', 'danger')
        return redirect(url_for('evaluations.list_exams', course_id=exam.course_id))

    if exam.has_been_taken_by(current_user):
        flash('Ya rendiste este examen.', 'info')
        return redirect(url_for('evaluations.view_result', exam_id=exam_id))

    if exam.total_questions() == 0:
        flash('Este examen todavía no tiene preguntas.', 'warning')
        return redirect(url_for('evaluations.list_exams', course_id=exam.course_id))

    questions = exam.questions

    return render_template('evaluations/take_exam.html',
                           exam=exam,
                           course=course,
                           school=course.school,
                           questions=questions)


# ──────────────────────────────────────────────
#  ENVIAR respuestas del examen
# ──────────────────────────────────────────────

@evaluations_bp.route('/exam/<int:exam_id>/submit', methods=['POST'])
@login_required
def submit_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    course = _get_course_or_404(exam.course_id)

    if not course.is_member(current_user) or not course.is_alumno(current_user):
        abort(403)

    if exam.has_been_taken_by(current_user):
        flash('Ya rendiste este examen.', 'info')
        return redirect(url_for('evaluations.view_result', exam_id=exam_id))

    questions = exam.questions
    score = 0

    for question in questions:
        chosen = request.form.get(f'question_{question.id}')
        if chosen in ('a', 'b', 'c', 'd'):
            answer = StudentAnswer(
                question_id=question.id,
                student_id=current_user.id,
                chosen_option=chosen
            )
            db.session.add(answer)
            if chosen == question.correct_option:
                score += 1

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
#  VER RESULTADO
# ──────────────────────────────────────────────

@evaluations_bp.route('/exam/<int:exam_id>/result')
@login_required
def view_result(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    course = _get_course_or_404(exam.course_id)

    grade = exam.get_grade_for(current_user)
    if not grade:
        flash('Todavía no rendiste este examen.', 'info')
        return redirect(url_for('evaluations.list_exams', course_id=exam.course_id))

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
                           school=course.school,
                           grade=grade,
                           answers=answers)


# ──────────────────────────────────────────────
#  VER NOTAS (profesor/admin en el colegio)
# ──────────────────────────────────────────────

@evaluations_bp.route('/exam/<int:exam_id>/grades')
@login_required
def view_grades(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    course = _get_course_or_404(exam.course_id)
    _require_profesor_of(course)

    grades = Grade.query.filter_by(exam_id=exam_id).order_by(Grade.created_at.desc()).all()

    return render_template('evaluations/view_grades.html',
                           exam=exam,
                           course=course,
                           school=course.school,
                           grades=grades)


# ──────────────────────────────────────────────
#  ELIMINAR examen (profesor/admin en el colegio)
# ──────────────────────────────────────────────

@evaluations_bp.route('/exam/<int:exam_id>/delete', methods=['POST'])
@login_required
def delete_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    course = _get_course_or_404(exam.course_id)
    _require_profesor_of(course)

    course_id = exam.course_id
    db.session.delete(exam)
    db.session.commit()

    flash('Examen eliminado.', 'info')
    return redirect(url_for('evaluations.list_exams', course_id=course_id))
