import os
from flask import Flask, request, jsonify
import requests
from langdetect import detect

app = Flask(__name__)

# ✅ Use the Mistral model from Hugging Face
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
HUGGINGFACE_TOKEN = os.environ.get("HF_TOKEN")  # Make sure the token is set in environment variables

headers = {
    "Authorization": f"Bearer {HUGGINGFACE_TOKEN}"
}

# ✅ System prompt: Defines the assistant's scope and limitations
SYSTEM_PROMPT = (
    "You are a helpful assistant named 'Tofy', specialized only in answering questions related to private and international universities in Egypt.\n"
    "✅ Your job is to help users find suitable universities or colleges based on tuition fees, available programs, admission requirements, and study systems.\n"
    "❌ Do NOT answer any questions outside the scope of private or international universities in Egypt.\n"
    "❌ Do NOT provide information about public (governmental) universities.\n"
    "❌ If a user asks about anything outside that scope, politely decline and remind them of your specialization.\n"
    "Only respond with clear, accurate, and helpful information based on private and international education in Egypt."
)

# Bot introduction messages
BOT_INTRO = {
    "en": (
        "Hello, I'm Tofy 👋\n"
        "I'm here to help you find the best private or international university and college in Egypt based on your needs.\n"
        "You can ask me about tuition fees, programs, admission requirements, and more. Just type your question!"
    ),
    "ar": (
        "أهلاً! أنا توفي 🤖\n"
        "موجود علشان أساعدك تلاقي أفضل جامعة أو كلية خاصة أو دولية في مصر.\n"
        "اسألني عن المصاريف، التخصصات، شروط التقديم، وأي حاجة تانية!"
    )
}

# In-memory session storage
session_memory = {}

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_id = data.get("user_id")
    user_input = data.get("question", "").strip()

    if not user_id or not user_input:
        return jsonify({"error": "Both 'user_id' and 'question' are required."}), 400

    # Detect language of the input
    try:
        lang = detect(user_input)
    except:
        lang = "en"

    # Greeting/intro message
    if user_input.lower() in ["hi", "hello", "start", "who are you", "introduce yourself", "ابدأ", "مرحبا", "من أنت"]:
        return jsonify({"answer": BOT_INTRO.get(lang, BOT_INTRO["en"])})

    # Initialize session with system prompt
    if user_id not in session_memory:
        session_memory[user_id] = [f"System: {SYSTEM_PROMPT}"]

    session_memory[user_id].append(f"User: {user_input}")
    prompt = "\n".join(session_memory[user_id]) + "\nAssistant:"

    try:
        response = requests.post(
            HUGGINGFACE_API_URL,
            headers=headers,
            json={"inputs": prompt}
        )

        if response.status_code != 200:
            raise Exception(f"Hugging Face API error: {response.text}")

        generated = response.json()[0]["generated_text"].split("Assistant:")[-1].strip()
        session_memory[user_id].append(f"Assistant: {generated}")

        return jsonify({"answer": generated})

    except Exception as e:
        fallback_msg = {
            "en": "I'm still learning, so I might not have all the answers yet. But I'm doing my best to improve every day! 😊",
            "ar": "أنا لسه بتعلم، فممكن تكون في حاجات لسه معرفهاش. بس بوعدك إني بحاول أتحسن كل يوم! 😊"
        }

        return jsonify({"answer": fallback_msg.get(lang, fallback_msg["en"])}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))








