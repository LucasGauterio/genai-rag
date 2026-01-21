from flask import Flask
from flask_cors import CORS

from api import sessions_bp, generation_bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(sessions_bp, url_prefix="/api")
    app.register_blueprint(generation_bp, url_prefix="/api")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
