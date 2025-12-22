from flask import Flask
from flask_cors import CORS

from api.chat import chat_bp
from api.ingest import ingest_bp

def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(ingest_bp, url_prefix="/api")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
