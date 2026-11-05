def create_app():
    # Lazy imports keep pure validation/grounding modules testable without Flask.
    from flask import Flask

    from .views import bp

    app = Flask(__name__)
    app.register_blueprint(bp)
    return app
