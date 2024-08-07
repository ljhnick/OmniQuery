from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS

import pyrootutils
pyrootutils.setup_root(__file__, indicator=".project-root", pythonpath=True)

from main_web import initialize, retrieve

import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/init', methods=['POST'])
def init():
    initialize()
    try:
        # Initialization process
        return jsonify({"status": "Memory initialized"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/query', methods=['POST'])
def query():
    data = request.get_json(force=True)
    text = data['text']

    # start_query()
    result = retrieve(text)
    # answer = result['answer']
    # images = result['images']
    # time_cost = result['time_cost']
    # cost = result['cost']

    # for image in image_transfers:
    #     img = send_file(image, mimetype='image/jpeg')

    return jsonify(result)
    # return jsonify({'answer': answer, 'images': images})


if __name__ == '__main__':
    app.run(debug=True)