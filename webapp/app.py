import speech_recognition
from elasticsearch import Elasticsearch
from flask import Flask, render_template, request, jsonify
from config.dev import ELASTICHOST, ELASTICINDEX

r = speech_recognition.Recognizer()

app = Flask(__name__)
es = Elasticsearch([ELASTICHOST])


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/recognize', methods=['POST'])
def recognize():
    file = request.files['file']
    recognizer = speech_recognition.Recognizer()
    audio_file = speech_recognition.AudioFile(file)
    with audio_file as source:
        audio_data = recognizer.record(source)
    text = recognizer.recognize_google(audio_data)
    req = {
        'min_score': 25,
        'query': {
            'bool': {
                'must': [
                    {
                        'match': {'lyric': text}
                    }
                ]
            }
        }
    }
    doc = es.search(index=ELASTICINDEX, body=req)
    if not doc['hits']['hits']:
        return jsonify({'data': None})
    return jsonify({'data': doc['hits']['hits'][0]['_source']})


if __name__ == '__main__':
    app.run()
