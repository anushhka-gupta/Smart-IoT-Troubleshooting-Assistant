import os
import json
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
CORS(app)

# ── Model configuration ──────────────────────────────────────────────────────
# Model : openai/gpt-oss-120b  served via Groq's OpenAI-compatible endpoint
# Docs  : https://console.groq.com/docs/openai
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL_NAME   = os.getenv("MODEL_NAME",   "openai/gpt-oss-120b")

# OpenAI client pointed at Groq's base URL
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

# ── System prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert Smart IoT Device Troubleshooting Assistant.
Your role is to help users diagnose and resolve issues with IoT devices including:
- Smart home devices (lights, thermostats, door locks, cameras)
- Network & connectivity problems (Wi-Fi, Zigbee, Z-Wave, Bluetooth, Matter)
- Sensor malfunctions (temperature, humidity, motion, water leak)
- Voice assistants integration (Alexa, Google Home, Apple HomeKit, Siri)
- Firmware & software update issues
- Power and battery problems
- Cloud connectivity and app synchronization
- Security vulnerabilities and best practices

Guidelines:
1. Ask clarifying questions to pinpoint the exact issue.
2. Provide step-by-step troubleshooting instructions that are easy to follow.
3. Suggest both quick fixes and long-term solutions.
4. Mention when a factory reset or professional help is needed.
5. Be concise yet thorough. Use numbered steps for procedures.
6. If the issue is outside IoT troubleshooting scope, politely redirect.

Always start by identifying: the device type, brand/model if known, the symptom, and how long the issue has been occurring."""

# ── In-memory conversation history per session ───────────────────────────────
conversation_histories: dict[str, list[dict]] = {}


def get_history(session_id: str) -> list[dict]:
    if session_id not in conversation_histories:
        conversation_histories[session_id] = []
    return conversation_histories[session_id]


def build_messages(history: list[dict]) -> list[dict]:
    """Prepend the system prompt to the conversation history."""
    return [{"role": "system", "content": SYSTEM_PROMPT}] + history




# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """Standard (non-streaming) chat endpoint."""
    data = request.get_json(silent=True)
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field"}), 400

    user_message: str = data["message"].strip()
    session_id: str   = data.get("session_id", "default")

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    history = get_history(session_id)
    history.append({"role": "user", "content": user_message})

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=build_messages(history),
            max_tokens=1024,
            temperature=0.7,
        )
        assistant_message = completion.choices[0].message.content
        history.append({"role": "assistant", "content": assistant_message})

        return jsonify({"response": assistant_message, "session_id": session_id})

    except Exception as e:
        return jsonify({"error": f"Groq API error: {str(e)}"}), 503


@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    """Server-Sent Events streaming chat endpoint."""
    data = request.get_json(silent=True)
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field"}), 400

    user_message: str = data["message"].strip()
    session_id: str   = data.get("session_id", "default")

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    history = get_history(session_id)
    history.append({"role": "user", "content": user_message})
    messages = build_messages(history)

    def generate():
        full_response: list[str] = []
        try:
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    full_response.append(delta)
                    yield f"data: {json.dumps({'token': delta})}\n\n"

            complete = "".join(full_response)
            history.append({"role": "assistant", "content": complete})
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/reset", methods=["POST"])
def reset():
    """Clear conversation history for a session."""
    data = request.get_json(silent=True) or {}
    session_id: str = data.get("session_id", "default")
    conversation_histories.pop(session_id, None)
    return jsonify({"message": "Conversation cleared", "session_id": session_id})


@app.route("/api/health", methods=["GET"])
def health():
    """Health check — confirms Groq client is configured."""
    return jsonify({
        "status": "ok",
        "provider": "Groq API (OpenAI-compatible)",
        "model": MODEL_NAME,
        "model_ready": True,
        "token_set": bool(GROQ_API_KEY),
    })


@app.route("/api/suggestions", methods=["GET"])
def suggestions():
    """Return starter troubleshooting prompts."""
    starters = [
        "My smart light bulb won't connect to Wi-Fi",
        "My Nest thermostat is showing offline in the app",
        "Motion sensor keeps triggering false alerts",
        "Smart door lock battery drains in 2 days",
        "Google Home can't discover my new device",
        "Smart plug not responding after power outage",
        "Security camera video feed is lagging",
        "Zigbee devices randomly disconnect from hub",
        "Firmware update failed on my smart TV",
        "HomeKit automation stopped working after iOS update",
    ]
    return jsonify({"suggestions": starters})


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🤖  IoT Troubleshooting Chatbot — Groq API")
    print(f"   Model  : {MODEL_NAME}")
    print(f"   API Key: {'SET ✓' if GROQ_API_KEY else 'NOT SET — add GROQ_API_KEY to .env'}")
    print("   URL    : http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
