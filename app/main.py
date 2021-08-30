import base64
import json
import os
import io
from http.client import HTTPException
from flask_cors import CORS, cross_origin
import speech_recognition as sr
from flask import Flask, jsonify,request,send_file
import random
import string
from google.cloud import texttospeech
from werkzeug.exceptions import BadRequest

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="google_keys.json"

N=10
@app.route('/speechToTextAudio', methods=['POST'])
@cross_origin()
def speechToTextAudio():
    r = sr.Recognizer()
    with open('audio.wav', 'wb') as f:
        f.write(request.files['file'].stream.read())
    with sr.AudioFile('audio.wav') as source:
        audio_data = r.record(source)
        text = r.recognize_google(audio_data, language='en-IN', show_all=True)
        if len(text) == 0:
            return '{"error": "SPEECH_TO_TEXT_FAILED"}', 400
        else:
            resp=text['alternative'][0]
        return json.dumps(resp)


@app.route('/speechToTextVideo', methods=['POST'])
@cross_origin()
def speechToTextVideo():
    keyName = ''.join(random.choices(string.ascii_uppercase + string.digits, k=N))
    r = sr.Recognizer()
    generatedVideo = 'video' + keyName + '.mp4'
    generatedAudio = 'audio' + keyName + '.wav'
    file_bytes = request.files['file'].stream.read()
    if len(file_bytes) == 0:
        return '{"error": "SPEECH_TO_TEXT_FAILED_EMPTY_FILE"}', 400
    with open(generatedVideo, 'wb') as f:
        f.write(file_bytes)

    os.system(
        'ffmpeg -y -i {} -acodec pcm_s16le -ar 16000 {}'.format(generatedVideo, generatedAudio))
    with sr.AudioFile(generatedAudio) as source:
        audio_data = r.record(source)
        text = r.recognize_google(audio_data, language='en-IN', show_all=True)
        if len(text) == 0:
            return '{"error": "SPEECH_TO_TEXT_FAILED"}', 400
        else:
            resp=text['alternative'][0]
            return json.dumps(resp)

@app.route('/textToSpeech', methods=['GET'])
@cross_origin()
def textToSpeech():
    if 'textToRead' in request.args:
        # Instantiates a client
        client = texttospeech.TextToSpeechClient()

        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=request.args['textToRead'])

        # Build the voice request, select the language code ("en-US") and the ssml
        # voice gender ("neutral")
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        # Select the type of audio file you want returned
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16
        )

        # Perform the text-to-speech request on the text input with the selected
        # voice parameters and audio file type
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        base64_encoded_data = base64.b64encode(response.audio_content)
        base64_message = base64_encoded_data.decode('utf-8')

        resp = {
            "statusCode": "200",
            "statusMessage": "SUCCESS",
            "data": base64_message,
        }
        return json.dumps(resp)
    else:
        raise BadRequest ("textToRead does not exist")
@app.errorhandler(HTTPException)
def handleException(e):
    response = e.get_response()
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response

if __name__ == '__main__':
    app.run(host= '0.0.0.0')

