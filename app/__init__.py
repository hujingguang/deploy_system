from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
app = Flask(__name__)
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
app.config['SECRET_KEY']='123123123123123'
app.config['SQLALCHEMY_DATABASE_URI']='mysql://hoo:hoo123@xx.x.x.x/hoo'
app.config['CSRF_ENABLED']=True
app.config['SQLALCHEMY_ECHO']=True
app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', True)
from app import views,models
