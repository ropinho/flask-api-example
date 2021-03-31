from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/greeting')
def greeting():
    return {'msg': 'Hello, World from Flask!'}

