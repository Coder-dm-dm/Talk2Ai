from flask import Flask
from twilio.twiml.voice_response import VoiceResponse
from google import genai

def sayai():
    client = genai.Client(api_key="AIzaSyCOcYyAff14TgLBWs1XN1lU3DJxAi4fY5g")

    response = client.models.generate_content(
        model="gemma-3-27b-it",
        contents="explain photosynthesisin 50 words",
    )
    return str("Explain photosynthesis . . . . " + response.text)

    

app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def hello_monkey():
    """Respond to incoming calls with a simple text message."""

    resp = VoiceResponse()
    resp.say(sayai())
    return str(resp)



if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)