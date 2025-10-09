from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."

    # Register blueprints
    from .routes import auth, manager, team_leader, counter, api
    app.register_blueprint(api.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(manager.bp)
    app.register_blueprint(team_leader.bp)
    app.register_blueprint(counter.bp)

    # ✅ Flask 3.1 fix: run initialization code right after app creation
    with app.app_context():
        db.create_all()
        if not User.query.first():
            default_manager = User(
                username="Admin_manager",
                password_hash=generate_password_hash("admin123"),
                role="Manager",
                is_active=True
            )
            db.session.add(default_manager)
            db.session.commit()
            print("✅ Default Manager user created: Admin_manager / admin123")

    return app