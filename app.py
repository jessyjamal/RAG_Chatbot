import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"
HUGGINGFACE_TOKEN = os.environ.get("HF_TOKEN")  # خزنيه في متغير بيئة

headers = {
    "Authorization": f"Bearer {HUGGINGFACE_TOKEN}"
}

# Bot intro
BOT_INTRO = (
    "Hello, I'm Tofy 👋\n"
    "I'm here to help you find the best private or international university and college in Egypt based on your needs.\n"
    "You can ask me about tuition fees, programs, admission requirements, and more. Just type your question!"
)

# Session memory
session_memory = {}

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_id = data.get("user_id")
    user_input = data.get("question", "").strip()

    if not user_id or not user_input:
        return jsonify({"error": "Both 'user_id' and 'question' are required."}), 400

    if user_input.lower() in ["hi", "hello", "start", "who are you", "introduce yourself"]:
        return jsonify({"answer": BOT_INTRO})

    # Initialize session
    if user_id not in session_memory:
        session_memory[user_id] = []

    session_memory[user_id].append(f"User: {user_input}")
    prompt = "\n".join(session_memory[user_id]) + "\nAssistant:"

    try:
        response = requests.post(
            HUGGINGFACE_API_URL,
            headers=headers,
            json={"inputs": prompt}
        )

        if response.status_code != 200:
            return jsonify({"error": f"Hugging Face error: {response.text}"}), 500

        generated = response.json()[0]["generated_text"].split("Assistant:")[-1].strip()
        session_memory[user_id].append(f"Assistant: {generated}")

        return jsonify({"answer": generated})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))



