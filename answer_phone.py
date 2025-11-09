# app.py -- Step 4: Error Handling & Loop
import os
import re
import logging
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from google import genai
# near top of app.py
from dashboard import read_prompt
import logging
from logging.handlers import RotatingFileHandler



app = Flask(__name__)
# after app = Flask(__name__)

LOG_FILE = os.environ.get("APP_LOG_FILE", "app.log")
handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=2)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.config["APP_LOG_FILE"] = LOG_FILE
from dashboard import bp as dashboard_bp
app.register_blueprint(dashboard_bp)

logging.basicConfig(level=logging.INFO)

GENAI_API_ENV = "GOOGLE_GENAI_API_KEY"
MODEL_NAME = "gemma-3-27b-it"

# ---------------------------------------------
# Helper: GenAI client
# ---------------------------------------------
def get_genai_client():
    api_key = os.environ.get(GENAI_API_ENV)
    if not api_key:
        raise RuntimeError(f"Missing {GENAI_API_ENV}")
    return genai.Client(api_key=api_key)

# ---------------------------------------------
# Helper: LLM call
# ---------------------------------------------
def ask_teacher(prompt: str) -> str:
    client = get_genai_client()
    try:
        resp = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        if not resp or not getattr(resp, "text", None):
            raise RuntimeError("Empty response from model")
        return resp.text.strip()
    except Exception as e:
        logging.exception("Gemma API call failed: %s", e)
        return None

# ---------------------------------------------
# Helper: Text-to-speech pacing
# ---------------------------------------------
def tts_speak(resp: VoiceResponse, text: str):
    text = re.sub(r"\s+", " ", text)
    sentences = re.split(r"(?<=[.!?]) +", text)
    for s in sentences:
        if not s.strip():
            continue
        resp.say(s.strip(), voice="alice", language="en-US")
        resp.pause(length=1.0)

# ---------------------------------------------
# Helper: Start a new question loop
# ---------------------------------------------
def ask_follow_up(resp: VoiceResponse, prompt_msg="Would you like to ask another question?"):
    gather = Gather(
        input="speech",
        action="/gather_followup",
        method="POST",
        timeout=5,
        speech_timeout="auto"
    )
    gather.say(prompt_msg, voice="alice", language="en-US")
    resp.append(gather)
    resp.say("Goodbye for now!", voice="alice")
    resp.hangup()

# ---------------------------------------------
# Route: First inbound call
# ---------------------------------------------
@app.route("/", methods=["GET", "POST"])
def inbound_call():
    resp = VoiceResponse()
    gather = Gather(
        input="speech",
        action="/gather_response",
        method="POST",
        timeout=5,
        speech_timeout="auto"
    )
    gather.say(
        "Hello again! I’m your learning assistant teacher. "
        "Ask your question now",
        voice="alice", language="en-US"
    )
    
    resp.append(gather)
    resp.say("I didn’t hear a question. Goodbye!", voice="alice")
    resp.hangup()
    return str(resp)

# ---------------------------------------------
# Route: Handle initial question
# ---------------------------------------------
@app.route("/gather_response", methods=["POST"])
def gather_response():
    speech_text = (request.values.get("SpeechResult") or "").strip()
    resp = VoiceResponse()

    if not speech_text:
        resp.say("Sorry, I didn’t catch that.", voice="alice")
        ask_follow_up(resp)
        return str(resp)

    logging.info(f"Student asked: {speech_text}")

    base_prompt = read_prompt() or (
    "You are a kind, encouraging teacher speaking to a young student over the phone. "
    "Explain concepts clearly and slowly in one or two short sentences. "
    "Avoid long words. End with a gentle encouragement like 'Good job!' or 'Keep learning!'. "
    )

    prompt = f"{base_prompt} Student asked: \"{speech_text}\""


    answer = ask_teacher(prompt)
    if not answer:
        resp.say("Sorry, I’m having trouble getting the answer right now.", voice="alice")
        ask_follow_up(resp)
        return str(resp)

    resp.say("Here’s what I found:", voice="alice")
    resp.pause(length=1.0)
    tts_speak(resp, answer)
    ask_follow_up(resp)
    return str(resp)

# ---------------------------------------------
# Route: Handle follow-up question
# ---------------------------------------------
@app.route("/gather_followup", methods=["POST"])
def gather_followup():
    speech_text = (request.values.get("SpeechResult") or "").lower().strip()
    resp = VoiceResponse()

    # If user says “no”, end call
    if any(phrase in speech_text for phrase in ["no", "nope", "nothing", "bye"]):
        resp.say("Okay! Goodbye and keep learning!", voice="alice")
        resp.hangup()
        return str(resp)

    # If empty, end politely
    if not speech_text:
        resp.say("I didn’t catch that. Let’s stop here for now. Goodbye!", voice="alice")
        resp.hangup()
        return str(resp)

    logging.info(f"Follow-up question: {speech_text}")

    prompt = (
        "Continue acting as a friendly teacher. "
        "Give a short, clear spoken answer, two sentences maximum. "
        f"Student asked: \"{speech_text}\""
    )

    answer = ask_teacher(prompt)
    if not answer:
        resp.say("Sorry, I can’t reach the teacher service right now.", voice="alice")
        ask_follow_up(resp)
        return str(resp)

    resp.say("Here’s another explanation:", voice="alice")
    resp.pause(length=1.0)
    tts_speak(resp, answer)
    ask_follow_up(resp)
    return str(resp)

# ---------------------------------------------
# Run the app
# ---------------------------------------------
if __name__ == "__main__":
    if not os.environ.get(GENAI_API_ENV):
        logging.warning("⚠️ Missing GOOGLE_GENAI_API_KEY environment variable.")
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
