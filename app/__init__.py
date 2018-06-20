from flask import Flask
app = Flask(__name__)
from app import views


SESSION_TYPE = 'redis'
app.config.from_object(__name__)
app.secret_key = 'gpodd3rp0d$iLL@'
