from dotenv import load_dotenv
load_dotenv('.flaskenv')

from app import app
import os



if __name__ == "__main__":
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_RUN_PORT', '5000'))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
   
    app.run(host=host, port=port, debug=debug)