# app/modules/courses/forms.py
"""
Formularios del módulo de cursos.

Usamos Flask-WTF (WTForms) para validar los datos del formulario
del lado del servidor. Cada campo tiene validators que checkean
que no vengan vacíos, que tengan cierta longitud, etc.

Los forms se instancian en la ruta (routes.py) y se pasan al template.
En el template se renderizan con {{ form.field.label }} y {{ form.field() }}.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, Email


class CourseForm(FlaskForm):
    """
    Formulario para crear o editar un curso.

    Se usa tanto en la ruta POST /courses/new (crear)
    como en POST /courses/<id>/edit (editar).
    En edición se precargan los valores con obj=curso.
    """
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


class AddStudentForm(FlaskForm):
    """
    Formulario para que un profesor agregue un alumno a su curso por email.

    El profesor escribe el email del alumno, se busca en la tabla users,
    y si existe y es alumno, se crea la inscripción.
    """
    email = StringField(
        'Email del alumno',
        validators=[
            DataRequired(message='Ingresá el email del alumno'),
            Email(message='Ingresá un email válido')
        ]
    )
    submit = SubmitField('Agregar alumno')
