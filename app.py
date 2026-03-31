from flask import Flask
from flask_mail import Mail
from flask_login import LoginManager
from config import Config
from models import db, User

mail = Mail()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please login to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.user import user_bp
    from routes.subject_staff import staff_bp
    from routes.tutor import tutor_bp
    from routes.hod import hod_bp
    from routes.coordinator import coordinator_bp
    from routes.admin import admin_bp
    from routes.main import main_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(staff_bp, url_prefix='/staff')
    app.register_blueprint(tutor_bp, url_prefix='/tutor')
    app.register_blueprint(hod_bp, url_prefix='/hod')
    app.register_blueprint(coordinator_bp, url_prefix='/coordinator')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(main_bp)

    # Create DB
    with app.app_context():
        db.create_all()
        from utils.seed import seed_admin
        seed_admin()

    return app


# ✅ RUN APP
if __name__ == '__main__':
    app = create_app()

    print("MAIL PORT:", app.config['MAIL_PORT'])
    print("TLS:", app.config['MAIL_USE_TLS'])
    print("SSL:", app.config['MAIL_USE_SSL'])

    app.run(debug=True)