from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin):
    def __init__(self, id, email, password_hash, role):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.role = role

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'