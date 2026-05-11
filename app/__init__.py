from flask import Flask, session, render_template
from .config import Config
from .extensions import db, login_manager, limiter
from .utils import get_settings

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Translations helper
    from .translations import TRANSLATIONS, get_lang, t
    app.jinja_env.globals['t'] = t
    app.jinja_env.globals['get_lang'] = get_lang
    app.jinja_env.globals['now'] = datetime.utcnow
    from .models import IRAQ_CITIES, CAR_BRANDS, CAR_BRAND_LOGOS
    app.jinja_env.globals['IRAQ_CITIES'] = IRAQ_CITIES
    app.jinja_env.globals['CAR_BRANDS'] = CAR_BRANDS
    app.jinja_env.globals['CAR_BRAND_LOGOS'] = CAR_BRAND_LOGOS

    # Language switcher route
    @app.route('/set_lang/<lang>')
    def set_lang(lang):
        if lang in ('ku', 'ar', 'en'):
            session['lang'] = lang
        return redirect(request.referrer or url_for('main.index'))

    # Register blueprints
    from .auth.routes import auth_bp
    from .main.routes import main_bp
    from .parts.routes import parts_bp
    from .reels.routes import reels_bp
    from .chat.routes import chat_bp
    from .payments.routes import payments_bp
    from .admin.routes import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(parts_bp, url_prefix='/parts')
    app.register_blueprint(reels_bp, url_prefix='/reels')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(payments_bp, url_prefix='/payment')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template('500.html'), 500

    return app
