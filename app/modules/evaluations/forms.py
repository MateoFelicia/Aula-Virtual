# app/modules/evaluations/forms.py
"""
Formularios del módulo de evaluaciones.

Hay dos forms principales:
  1. ExamForm: para crear/editar un examen (título, descripción, tiempo).
  2. QuestionForm: para agregar una pregunta al examen (texto + 4 opciones + correcta).

El flujo es:
  - Profesor crea el examen → ExamForm
  - Profesor agrega preguntas una por una → QuestionForm
  - Alumno responde con RadioFields → AnswerFormSet (manejado en la ruta)
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, RadioField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class ExamForm(FlaskForm):
    """Formulario para crear o editar un examen."""

    title = StringField(
        'Título del examen',
        validators=[
            DataRequired(message='El título es obligatorio'),
            Length(max=150)
        ]
    )
    description = TextAreaField(
        'Descripción / Instrucciones',
        validators=[Optional(), Length(max=500)]
    )
    time_limit = IntegerField(
        'Tiempo límite en minutos (vacío = sin límite)',
        validators=[
            Optional(),
            NumberRange(min=1, message='El tiempo debe ser al menos 1 minuto')
        ]
    )
    submit = SubmitField('Guardar examen')


class QuestionForm(FlaskForm):
    """
    Formulario para agregar una pregunta a un examen.
    Se muestra una vez por cada pregunta que el profesor quiera crear.
    """

    text = TextAreaField(
        'Pregunta',
        validators=[
            DataRequired(message='La pregunta es obligatoria'),
            Length(max=500)
        ]
    )
    option_a = StringField(
        'Opción A',
        validators=[DataRequired(message='Completá la opción A'), Length(max=255)]
    )
    option_b = StringField(
        'Opción B',
        validators=[DataRequired(message='Completá la opción B'), Length(max=255)]
    )
    option_c = StringField(
        'Opción C',
        validators=[DataRequired(message='Completá la opción C'), Length(max=255)]
    )
    option_d = StringField(
        'Opción D',
        validators=[DataRequired(message='Completá la opción D'), Length(max=255)]
    )
    correct_option = RadioField(
        'Respuesta correcta',
        choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')],
        validators=[DataRequired(message='Indicá cuál es la respuesta correcta')]
    )
    submit = SubmitField('Agregar pregunta')
