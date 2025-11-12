import json
import os
import logging
import time
from flask import Blueprint, current_app, jsonify, request, render_template, Response

bp = Blueprint(
    "dashboard",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/dashboard"
)

PROMPT_FILE = os.environ.get("PROMPT_FILE", "prompt_store.json")

PRESETS = {
    "english_assistant": (
        "You are a kind, encouraging English teacher speaking to a young student over the phone. "
        "Help the student with grammar, vocabulary, and pronunciation in a simple way. "
        "Explain clearly and slowly in one or two short sentences. Avoid long words. "
        "End with a gentle encouragement like 'Good job!' or 'Keep learning!'."
    ),
    "social_studies_assistant": (
        "You are a kind, encouraging social studies teacher speaking to a young student over the phone. "
        "Explain history, geography, and civic ideas clearly and simply in one or two short sentences. "
        "Avoid long words. End with a gentle encouragement like 'Good job!' or 'Keep learning!'."
    ),
    "science_assistant": (
        "You are a kind, encouraging science teacher speaking to a young student over the phone. "
        "Explain science ideas clearly and slowly in one or two short sentences. Avoid long words. "
        "End with a gentle encouragement like 'Good job!' or 'Keep learning!'."
    ),
    "math_assistant": (
        "You are a kind, encouraging math teacher speaking to a young student over the phone. "
        "Explain math concepts clearly and simply in one or two short sentences. "
        "End with a gentle encouragement like 'Good job!' or 'Keep learning!'."
    ),
}


def ensure_prompt_file():
    if not os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "w", encoding="utf-8") as f:
            json.dump({"prompt": ""}, f)

def read_prompt():
    ensure_prompt_file()
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("prompt", "")

def write_prompt(new_prompt: str):
    ensure_prompt_file()
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        json.dump({"prompt": new_prompt}, f)

@bp.route("/", methods=["GET"])
def index():
    return render_template("dashboard.html", presets=PRESETS)

@bp.route("/api/prompt", methods=["GET"])
def api_get_prompt():
    try:
        return jsonify({"prompt": read_prompt()})
    except Exception:
        current_app.logger.exception("Read prompt failed")
        return jsonify({"error": "failed reading prompt"}), 500

@bp.route("/api/prompt", methods=["POST"])
def api_set_prompt():
    data = request.get_json(silent=True)
    if not data or "prompt" not in data:
        return jsonify({"error": "missing prompt"}), 400
    new_prompt = data["prompt"]
    try:
        write_prompt(new_prompt)
        current_app.logger.info("Prompt updated via dashboard")
        return jsonify({"ok": True, "prompt": new_prompt})
    except Exception:
        current_app.logger.exception("Write prompt failed")
        return jsonify({"error": "failed writing prompt"}), 500

@bp.route("/api/preset/<name>", methods=["POST"])
def api_set_preset(name):
    preset = PRESETS.get(name)
    if not preset:
        return jsonify({"error": "unknown preset"}), 404
    try:
        write_prompt(preset)
        current_app.logger.info("Preset %s applied via dashboard", name)
        return jsonify({"ok": True, "prompt": preset})
    except Exception:
        current_app.logger.exception("Apply preset failed")
        return jsonify({"error": "failed applying preset"}), 500

@bp.route("/api/logs", methods=["GET"])
def api_logs():
    """Read static tail of log file."""
    log_path = current_app.config.get("APP_LOG_FILE", "app.log")
    lines = int(request.args.get("lines", 200))
    if not os.path.exists(log_path):
        return jsonify({"logs": "", "path": log_path})
    try:
        with open(log_path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            block = 4096
            data = b""
            while size > 0 and data.count(b"\n") < lines:
                read_size = min(block, size)
                f.seek(size - read_size)
                chunk = f.read(read_size)
                data = chunk + data
                size -= read_size
            text = data.decode("utf-8", errors="replace")
            last_lines = "\n".join(text.splitlines()[-lines:])
        return jsonify({"logs": last_lines, "path": log_path})
    except Exception:
        current_app.logger.exception("Failed reading logs")
        return jsonify({"error": "failed reading logs"}), 500

# --- SSE stream for live logs ---
@bp.route("/api/stream")
def api_stream():
    """Push live log updates to dashboard."""
    log_path = current_app.config.get("APP_LOG_FILE", "app.log")
    if not os.path.exists(log_path):
        open(log_path, "a").close()

    def stream():
        with open(log_path, "r", encoding="utf-8") as f:
            # Seek to end so only new logs are streamed
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(1)
                    continue
                yield f"data: {line.strip()}\n\n"

    return Response(stream(), mimetype="text/event-stream")
