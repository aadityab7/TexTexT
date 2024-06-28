from flask import Flask

# from flask_socketio import SocketIO
from project.extensions import socketio
from config import DevelopmentConfig, TestingConfig, ProductionConfig


def create_app(config_name="development"):
    app = Flask(__name__)
    # socketio = SocketIO(app)
    # Initialize extensions
    socketio.init_app(app)

    # Select the appropriate configuration class
    # and Load configuration from the config object
    if config_name == "development":
        app.config.from_object(DevelopmentConfig)
    elif config_name == "testing":
        app.config.from_object(TestingConfig)
    elif config_name == "production":
        app.config.from_object(ProductionConfig)
    else:
        raise ValueError(f"Invalid configuration name: {config_name}")

    # Register blueprints
    from .routes import main as main_blueprint

    app.register_blueprint(main_blueprint)

    return app, socketio
