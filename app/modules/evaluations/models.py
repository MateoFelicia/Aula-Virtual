# app/modules/evaluations/models.py
"""
Modelos del módulo de evaluaciones.

Exam:       un examen pertenece a un curso, tiene título y描述opcional.
Question:   cada pregunta pertenece a un examen, tiene 4 opciones (a/b/c/d)
            y guarda cuál es la correcta.
StudentAnswer: cada respuesta vincula una pregunta con un alumno.
            Guarda la opción que eligió el alumno.
Grade:      calificación final de un alumno en un examen.
            Se calcula al enviar: (respuestas correctas / total) * 100.

Flujo:
  1. Profesor crea Exam + Questions.
  2. Alumno entra al examen, responde las preguntas.
  3. Al enviar, se comparan las respuestas con las correctas,
     se calcula el score y se crea el Grade.
  4. El alumno puede ver su nota y qué preguntas falló.
"""
from app.extensions import db
from app.core.base_model import BaseModel


class Exam(BaseModel):
    __tablename__ = 'exams'

    # FK al curso al que pertenece el examen
    course_id = db.Column(
        db.Integer,
        db.ForeignKey('courses.id'),
        nullable=False
    )

    # Título del examen (ej: "Parcial 1 - Tema 3")
    title = db.Column(db.String(150), nullable=False)

    # Descripción opcional (instrucciones, tema, etc.)
    description = db.Column(db.Text, nullable=True)

    # Tiempo límite en minutos (NULL = sin límite de tiempo)
    time_limit = db.Column(db.Integer, nullable=True)

    # Relación 1 a N: un examen tiene muchas preguntas
    questions = db.relationship('Question', backref='exam', lazy=True, cascade='all, delete-orphan')

    # Relación 1 a N: un examen tiene muchas calificaciones
    grades = db.relationship('Grade', backref='exam', lazy=True, cascade='all, delete-orphan')

    def total_questions(self):
        """Cantidad total de preguntas del examen."""
        return len(self.questions)

    def has_been_taken_by(self, user):
        """Devuelve True si el usuario ya rindió este examen."""
        return Grade.query.filter_by(
            exam_id=self.id,
            student_id=user.id
        ).first() is not None

    def get_grade_for(self, user):
        """Devuelve la calificación del usuario en este examen, o None."""
        return Grade.query.filter_by(
            exam_id=self.id,
            student_id=user.id
        ).first()

    def __repr__(self):
        return f'<Exam {self.title}>'


class Question(BaseModel):
    __tablename__ = 'questions'

    # FK al examen al que pertenece esta pregunta
    exam_id = db.Column(
        db.Integer,
        db.ForeignKey('exams.id'),
        nullable=False
    )

    # Texto de la pregunta
    text = db.Column(db.Text, nullable=False)

    # Las 4 opciones de respuesta (obligatorias para opción múltiple)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)

    # Cuál es la respuesta correcta: 'a', 'b', 'c' o 'd'
    correct_option = db.Column(db.String(1), nullable=False)

    def __repr__(self):
        return f'<Question {self.id}: {self.text[:40]}>'


class StudentAnswer(BaseModel):
    __tablename__ = 'student_answers'

    # FK a la pregunta que se está respondiendo
    question_id = db.Column(
        db.Integer,
        db.ForeignKey('questions.id'),
        nullable=False
    )

    # FK al alumno que responde
    student_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    # Opción que eligió el alumno: 'a', 'b', 'c' o 'd'
    chosen_option = db.Column(db.String(1), nullable=False)

    # Relación para acceder fácilmente a la pregunta
    question = db.relationship('Question', backref='answers')

    # Evita que un alumno responda dos veces la misma pregunta
    __table_args__ = (
        db.UniqueConstraint('question_id', 'student_id', name='uq_question_student'),
    )

    def is_correct(self):
        """Devuelve True si la respuesta del alumno es correcta."""
        return self.chosen_option == self.question.correct_option

    def __repr__(self):
        return f'<Answer q={self.question_id} student={self.student_id} chose={self.chosen_option}>'


class Grade(BaseModel):
    __tablename__ = 'grades'

    # FK al examen
    exam_id = db.Column(
        db.Integer,
        db.ForeignKey('exams.id'),
        nullable=False
    )

    # FK al alumno
    student_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    # Cantidad de respuestas correctas
    score = db.Column(db.Integer, nullable=False)

    # Total de preguntas del examen
    total = db.Column(db.Integer, nullable=False)

    # Relación para acceder al alumno
    student = db.relationship('User', backref=db.backref('grades', lazy=True))

    # Evita que un alumno tenga dos calificaciones para el mismo examen
    __table_args__ = (
        db.UniqueConstraint('exam_id', 'student_id', name='uq_exam_student'),
    )

    def percentage(self):
        """Devuelve el porcentaje de aciertos (0-100)."""
        if self.total == 0:
            return 0
        return round((self.score / self.total) * 100)

    def __repr__(self):
        return f'<Grade exam={self.exam_id} student={self.student_id} score={self.score}/{self.total}>'
