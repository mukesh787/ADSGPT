from flask_bcrypt import Bcrypt
from flask import json, Flask, request
from flask_cors import CORS, cross_origin
import logging
import dynamo

app = Flask(__name__)
bcrypt = Bcrypt(app)
CORS(app)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
        
@app.route("/aiad/signup", methods=['POST'])
def signup():
    data = request.get_json()
    user_name = data['username']
    email = data['email']
    password = data['password']
    pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    dynamo.save_user(user_name, email, pw_hash)
    return (json.dumps({'success': 'succes'}), 200)

@app.route("/aiad/login", methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']
    items = dynamo.get_user(email)
    if len(items) > 0:
        item = items[0]
        pw_hash = item['password']
        is_valid = bcrypt.check_password_hash(pw_hash, password)
        if is_valid:
            return (json.dumps({'success': 'succes'}), 200)
        else:
            return (json.dumps({'message': 'Invalid password'}), 400)
        
    return (json.dumps({'message': 'Invalid password'}), 400)

if __name__ == "__main__":
  app.run(host='0.0.0.0', port=9090, debug=True)
  
  
  
