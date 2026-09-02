# app/modules/auth/models.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager
from app.core.base_model import BaseModel


class User(BaseModel, UserMixin):
    __tablename__ = 'users'

    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_school_role(self, school):
        from app.modules.schools.models import SchoolMember
        member = SchoolMember.query.filter_by(
            school_id=school.id,
            user_id=self.id
        ).first()
        return member.role if member else None

    def is_profesor_in(self, school):
        return self.get_school_role(school) == 'profesor'

    def is_alumno_in(self, school):
        return self.get_school_role(school) == 'alumno'

    def is_admin_in(self, school):
        return self.get_school_role(school) == 'admin'

    def __repr__(self):
        return f'<User {self.email}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
