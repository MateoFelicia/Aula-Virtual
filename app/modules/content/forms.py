# app/modules/content/forms.py
"""
Formulario para subir materiales a un curso.

Soporta dos modos:
  1. Subir un archivo (PDF, Word, video, etc.) — se guarda en disco.
  2. Pegar un enlace externo (YouTube, Google Drive, etc.) — solo se guarda la URL.

El campo 'material_type' se define en el form como RadioField para que
el profesor elija entre "Archivo" o "Enlace". Según la elección, se
muestra u oculta el campo correspondiente (eso se maneja con JS en el template).
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, RadioField, SubmitField
from wtforms.validators import DataRequired, Optional, URL, Length


class MaterialForm(FlaskForm):
    """Formulario para agregar un material a un curso."""

    title = StringField(
        'Título',
        validators=[
            DataRequired(message='El título es obligatorio'),
            Length(max=150)
        ]
    )
    description = TextAreaField(
        'Descripción (opcional)',
        validators=[Optional(), Length(max=500)]
    )
    material_type = RadioField(
        'Tipo de material',
        choices=[('file', 'Archivo'), ('link', 'Enlace')],
        default='file',
        validators=[DataRequired()]
    )
    file = FileField(
        'Seleccionar archivo',
        validators=[
            FileAllowed(
                ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx',
                 'mp4', 'avi', 'mov', 'zip', 'rar', 'txt', 'png', 'jpg', 'jpeg'],
                'Formato no permitido'
            )
        ]
    )
    external_url = StringField(
        'URL del enlace',
        validators=[Optional(), URL(message='Ingresá una URL válida')]
    )
    submit = SubmitField('Subir material')
