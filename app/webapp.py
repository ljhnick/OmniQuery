from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

import pyrootutils
pyrootutils.setup_root(__file__, indicator=".project-root", pythonpath=True)

from main import run_from_app

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_text', methods=['POST'])
def process_text():
    data = request.get_json(force=True)
    text = data['text']

    start_query()

    return jsonify({'processed_text': text.upper()})

def start_query():
    run_from_app()

if __name__ == '__main__':
    app.run(debug=True)