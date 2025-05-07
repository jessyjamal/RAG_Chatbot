import os
from flask import Flask, request, jsonify
import requests
from langdetect import detect

app = Flask(__name__)

# ✅ Use the OpenChat model from Hugging Face
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/openchat/openchat-3.5-0106"
HUGGINGFACE_TOKEN = os.environ.get("HF_TOKEN")  # Make sure the token is set in environment variables

headers = {
    "Authorization": f"Bearer {HUGGINGFACE_TOKEN}"
}

# Bot introduction messages in English and Arabic
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

# In-memory session storage per user
session_memory = {}

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_id = data.get("user_id")
    user_input = data.get("question", "").strip()

    if not user_id or not user_input:
        return jsonify({"error": "Both 'user_id' and 'question' are required."}), 400

    # Detect language of the user input
    try:
        lang = detect(user_input)
    except:
        lang = "en"

    # Respond with the bot introduction if greeting detected
    if user_input.lower() in ["hi", "hello", "start", "who are you", "introduce yourself", "ابدأ", "مرحبا", "من أنت"]:
        return jsonify({"answer": BOT_INTRO.get(lang, BOT_INTRO["en"])})

    # Initialize session memory if it's the user's first message
    if user_id not in session_memory:
        session_memory[user_id] = []

    # Append user input to session memory
    session_memory[user_id].append(f"User: {user_input}")
    prompt = "\n".join(session_memory[user_id]) + "\nAssistant:"

    try:
        # Send request to Hugging Face model
        response = requests.post(
            HUGGINGFACE_API_URL,
            headers=headers,
            json={"inputs": prompt}
        )

        if response.status_code != 200:
            raise Exception(f"Hugging Face API error: {response.text}")

        # Extract and clean the generated response
        generated = response.json()[0]["generated_text"].split("Assistant:")[-1].strip()
        session_memory[user_id].append(f"Assistant: {generated}")

        return jsonify({"answer": generated})
    except Exception as e:
        fallback_msg = {
            "en": "Sorry, I'm having trouble answering right now. Please try again later.",
            "ar": "عذراً، هناك مشكلة مؤقتة. حاول مرة أخرى لاحقاً."
        }
        return jsonify({"answer": fallback_msg.get(lang, fallback_msg["en"])}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))






