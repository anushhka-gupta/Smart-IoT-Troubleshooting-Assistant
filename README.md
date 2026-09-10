# 🤖 Smart IoT Device Troubleshooting Chatbot

An AI-powered multi-agent chatbot that provides real-time, personalized troubleshooting guidance for smart home and IoT devices. Built with Flask, Groq API, and the `openai/gpt-oss-120b` model.

---

## 📌 Domain

**Smart Home / Internet of Things (IoT)** — AI-driven troubleshooting assistant for connected devices and smart home ecosystems.

---

## 🧠 Overview

The Smart IoT Device Troubleshooting Chatbot helps users diagnose and resolve issues with IoT devices through an intelligent conversational interface. It uses a Retrieval-Augmented Generation (RAG) approach combined with Agentic AI to deliver accurate, context-aware, step-by-step device fix plans.

### Key Agents
| Agent | Role |
|---|---|
| **Device Knowledge Agent** | Retrieves device-specific troubleshooting info from manuals and protocol specs |
| **Diagnosis & Resolution Agent** | Generates personalized step-by-step fix plans based on device type and symptoms |
| **Preventive Maintenance Agent** | Provides proactive firmware, battery, and security recommendations |
| **Fault Log & Feedback Agent** | Analyzes user-reported faults and delivers instant root-cause analysis |

---

## ✨ Features

- 🔴 **Real-time streaming responses** via Server-Sent Events (SSE)
- 🧠 **Multi-turn conversation memory** — context retained per session
- 🏠 **IoT-specialized AI** — covers Wi-Fi, Zigbee, Z-Wave, Bluetooth, Matter protocols
- 💡 **10 quick-start prompts** for common device issues
- 📱 **Responsive dark-theme UI** with collapsible sidebar
- 🔒 **Secure API key handling** via environment variables
- ♻️ **New Conversation** button to reset session history

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| **Python / Flask** | Backend web framework |
| **Groq API** | LLM inference endpoint (OpenAI-compatible) |
| **openai/gpt-oss-120b** | Core language model for reasoning and diagnosis |
| **HTML / CSS / JavaScript** | Frontend chat interface |
| **IBM watsonx.ai** | Model deployment, embeddings, AI governance |
| **IBM Granite Models** | Natural language understanding and personalization |
| **IBM Bob Platform** | Multi-agent workflow orchestration |
| **RAG Pipeline** | Real-time device data retrieval before generation |
| **Vector Database (FAISS/Chroma)** | IoT knowledge base indexing and retrieval |
| **python-dotenv** | Secure environment variable management |

---

## 📁 Project Structure

```
Smart-IoT-Troubleshooting-Assistant/
│
├── app.py                  # Flask backend — API routes + LLM integration
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template (safe to share)
├── .gitignore              # Excludes .env, __pycache__, venv
│
├── templates/
│   └── index.html          # Chat UI — sidebar, welcome screen, streaming
│
└── static/
    └── style.css           # Dark-theme responsive stylesheet
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.9+
- A free Groq API key → [https://console.groq.com/keys](https://console.groq.com/keys)

### 1. Clone the Repository
```bash
git clone https://github.com/anushhka-gupta/Smart-IoT-Troubleshooting-Assistant.git
cd Smart-IoT-Troubleshooting-Assistant
```

### 2. Create a Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
# Copy the template
cp .env.example .env

# Open .env and add your Groq API key
GROQ_API_KEY=your_groq_api_key_here
MODEL_NAME=openai/gpt-oss-120b
```

### 5. Run the App
```bash
python app.py
```

Open your browser at **http://localhost:5000**

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the chat UI |
| `POST` | `/api/chat` | Standard (non-streaming) chat |
| `POST` | `/api/chat/stream` | SSE streaming chat |
| `POST` | `/api/reset` | Clears session conversation history |
| `GET` | `/api/health` | Health check — model and API status |
| `GET` | `/api/suggestions` | Returns quick-start troubleshooting prompts |

---

## 💬 Supported Device Categories

- 🏠 Smart Home (lights, thermostats, door locks, cameras)
- 📡 Networking (Wi-Fi, Zigbee, Z-Wave, Bluetooth, Matter)
- 🌡️ Sensors (temperature, humidity, motion, water leak)
- 🔒 Security (cameras, smart locks, vulnerability advice)
- 💡 Lighting (smart bulbs, LED strips, scenes)
- 🔌 Smart Plugs & Energy Monitors
- 🗣️ Voice Assistants (Alexa, Google Home, Siri, HomeKit)

---

## 🔒 Security Notes

- **Never commit your `.env` file** — it is blocked by `.gitignore`
- Use `.env.example` as a template — it contains no real secrets
- Rotate your Groq API key immediately if accidentally exposed
- The app reads `GROQ_API_KEY` only from the environment at runtime

---

## 🚀 Future Scope

1. **Smart Home Platform Integration** — Live device health data from Google Home, Alexa, HomeKit, and SmartThings for proactive diagnosis
2. **AI Voice Assistant & Multilingual Support** — Voice-based fault reporting in multiple languages for broader accessibility

---

## 📄 License

This project is intended for educational and demonstration purposes.

---

## 👩‍💻 Author

**Anushka Gupta**
[GitHub](https://github.com/anushhka-gupta) · Smart IoT Device Troubleshooting Assistant

