# app/modules/content/services.py
from app.core.base_service import BaseService
from .models import Material

class ContentService(BaseService):
    model = Material