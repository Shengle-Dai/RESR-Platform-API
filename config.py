import os

basedir = os.path.abspath(os.path.dirname(__file__))  # Get the absolute path of the current file

class Config(object):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
