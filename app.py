import os
from project import create_app

# Determine the configuration based on the environment variable
config_name = os.getenv('FLASK_CONFIG') or 'development'

# Create the Flask app with the specified configuration
app, socketio = create_app(config_name)

if __name__ == '__main__':
    socketio.run(
        app, 
        host = "0.0.0.0", 
        port = int(os.environ.get("PORT", 8000)), 
        allow_unsafe_werkzeug=True, 
        debug = True
    )