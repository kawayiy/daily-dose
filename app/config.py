import os
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-cannot-guess-this-ever'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir,'instance/app.db')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}

current_env = os.environ.get('FLASK_ENV', 'development')
CurrentConfig = config_by_name.get(current_env, DevelopmentConfig)