def create_app():
    from flask import Flask

    from .views import bp

    app = Flask(__name__)
    app.register_blueprint(bp)
    return app
