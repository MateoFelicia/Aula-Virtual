# app/modules/courses/routes.py
from flask import render_template
from . import courses_bp
from .services import CourseService


@courses_bp.route('/')
def index():
    courses = CourseService.get_all()
    return render_template('courses/index.html', courses=courses)