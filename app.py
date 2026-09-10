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
# Groq confirmed working models (as of 2025):
#   openai/gpt-oss-120b    ← default (most capable)
#   openai/gpt-oss-20b     ← lighter/faster
#   qwen/qwen3.6-27b       ← Qwen3 27B
#   groq/compound          ← Groq compound model
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL_NAME   = os.getenv("MODEL_NAME",   "openai/gpt-oss-120b")

if not GROQ_API_KEY:
    raise RuntimeError(
        "\n\n  ❌  GROQ_API_KEY is not set!\n"
        "  Create a .env file in this folder with:\n"
        "      GROQ_API_KEY=your_key_here\n"
        "  Get a free key at: https://console.groq.com/keys\n"
    )

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
        error_msg = str(e)
        if "401" in error_msg or "invalid_api_key" in error_msg.lower():
            return jsonify({"error": "Invalid Groq API key. Check your .env file."}), 401
        if "404" in error_msg or "model_not_found" in error_msg.lower() or "decommissioned" in error_msg.lower():
            return jsonify({"error": f"Model '{MODEL_NAME}' not available on Groq. Try openai/gpt-oss-120b."}), 404
        return jsonify({"error": f"Groq API error: {error_msg}"}), 503


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
            error_msg = str(e)
            if "401" in error_msg or "invalid_api_key" in error_msg.lower():
                yield f"data: {json.dumps({'error': 'Invalid Groq API key. Check your .env file.'})}\n\n"
            elif "404" in error_msg or "model_not_found" in error_msg.lower() or "decommissioned" in error_msg.lower():
                yield f"data: {json.dumps({'error': 'Model not available on Groq. Try openai/gpt-oss-120b.'})}\n\n"
            else:
                yield f"data: {json.dumps({'error': error_msg})}\n\n"

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
    """Health check — confirms Groq client is reachable."""
    try:
        # Lightweight probe: list models (no tokens consumed)
        models = client.models.list()
        available = [m.id for m in models.data]
        model_ready = MODEL_NAME in available
        return jsonify({
            "status": "ok",
            "provider": "Groq API (OpenAI-compatible)",
            "model": MODEL_NAME,
            "model_ready": model_ready,
            "token_set": True,
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "provider": "Groq API",
            "model": MODEL_NAME,
            "model_ready": False,
            "detail": str(e),
        }), 503


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
    print("=" * 50)
    print("🤖  Smart IoT Troubleshooting Chatbot")
    print("=" * 50)
    print(f"   Provider : Groq API")
    print(f"   Model    : {MODEL_NAME}")
    print(f"   API Key  : SET ✓")
    print(f"   URL      : http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)

    print(f"   Model  : {MODEL_NAME}")
    print(f"   API Key: {'SET ✓' if GROQ_API_KEY else 'NOT SET — add GROQ_API_KEY to .env'}")
    print("   URL    : http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
