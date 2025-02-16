from flask import Flask, request

app = Flask(__name__)

TOKEN = 'BULLSIT'

@app.route("/", methods=['GET', 'POST'])
def hello_world():
    data = request.args
    hub_challenge = data.get('hub.challenge')

    if hub_challenge:
        return hub_challenge
    else: 
        return "<p>Helloooo</p>"