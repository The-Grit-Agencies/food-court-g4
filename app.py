import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

base_dir = os.path.abspath(os.path.dirname(__file__))

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'wewewacha'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(base_dir, "main.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'static/menu_images'
    app.config['LOGO_UPLOAD_FOLDER'] = 'static/logos'
    app.config['PIC_UPLOAD_FOLDER'] = 'static/profile_pics'

    app.config['MAX_CONTENT_PATH'] = 16 * 1024 * 1024  # 16 MB max file size

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PIC_UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['LOGO_UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    from .routes import main
    app.register_blueprint(main)

    return app
