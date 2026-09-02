# app/modules/schools/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class CreateSchoolForm(FlaskForm):
    name = StringField(
        'Nombre del colegio',
        validators=[
            DataRequired(message='El nombre es obligatorio'),
            Length(max=150)
        ]
    )
    description = TextAreaField(
        'Descripción (opcional)',
        validators=[Length(max=500)]
    )
    submit = SubmitField('Crear colegio')


class JoinSchoolForm(FlaskForm):
    code = StringField(
        'Código del colegio',
        validators=[
            DataRequired(message='Ingresá el código del colegio'),
            Length(max=10)
        ]
    )
    submit = SubmitField('Unirse')


class AddMemberForm(FlaskForm):
    email = StringField(
        'Email del usuario',
        validators=[DataRequired(message='Ingresá el email')]
    )
    submit = SubmitField('Agregar miembro')
