# app/modules/courses/forms.py
"""
Formularios del módulo de cursos.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, Email


class CourseForm(FlaskForm):
    title = StringField(
        'Título del curso',
        validators=[
            DataRequired(message='El título es obligatorio'),
            Length(max=150, message='El título no puede tener más de 150 caracteres')
        ]
    )
    description = TextAreaField(
        'Descripción',
        validators=[
            Optional(),
            Length(max=1000, message='La descripción no puede tener más de 1000 caracteres')
        ]
    )
    capacity = IntegerField(
        'Capacidad máxima (vacío = sin límite)',
        validators=[
            Optional(),
            NumberRange(min=1, message='La capacidad debe ser al menos 1')
        ]
    )
    submit = SubmitField('Guardar curso')


class JoinCourseForm(FlaskForm):
    code = StringField(
        'Código del curso',
        validators=[
            DataRequired(message='Ingresá el código del curso'),
            Length(max=10)
        ]
    )
    submit = SubmitField('Unirse al curso')


class AddStudentForm(FlaskForm):
    email = StringField(
        'Email del alumno',
        validators=[
            DataRequired(message='Ingresá el email del alumno'),
            Email(message='Ingresá un email válido')
        ]
    )
    submit = SubmitField('Agregar alumno')
