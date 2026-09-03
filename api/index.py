import os
os.environ['FLASK_ENV'] = 'production'

from app import create_app

app = create_app('production')