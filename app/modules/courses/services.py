# app/modules/courses/services.py
from app.core.base_service import BaseService
from .models import Course

class CourseService(BaseService):
    model = Course