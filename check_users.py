from app import app
from models import User
from shared.db import db

with app.app_context():
    users = User.query.all()
    print(f'Total users: {len(users)}')
    for u in users:
        print(f'ID: {u.id}, Username: {u.username}, Email: {u.email}, Auth Provider: {u.auth_provider}, OAuth ID: {u.oauth_id}')
