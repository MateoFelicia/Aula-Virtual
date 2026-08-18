# app/modules/evaluations/services.py
from app.core.base_service import BaseService
from .models import Exam

class EvaluationService(BaseService):
    model = Exam