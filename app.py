import os
from flask import Flask, request, jsonify
import requests
from langdetect import detect

app = Flask(__name__)

# Hugging Face (Mixtral model)
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
HUGGINGFACE_TOKEN = os.environ.get("HF_TOKEN")

# Gemini API setup
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Headers
HF_HEADERS = {
    "Authorization": f"Bearer {HUGGINGFACE_TOKEN}"
}
GEMINI_HEADERS = {
    "Content-Type": "application/json"
}

# Bot intro
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

session_memory = {}

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_id = data.get("user_id")
    user_input = data.get("question", "").strip()

    if not user_id or not user_input:
        return jsonify({"error": "Both 'user_id' and 'question' are required."}), 400

    try:
        lang = detect(user_input)
    except:
        lang = "en"

    if user_input.lower() in ["hi", "hello", "start", "who are you", "introduce yourself", "ابدأ", "مرحبا", "من أنت"]:
        return jsonify({"answer": BOT_INTRO.get(lang, BOT_INTRO["en"])})

    if user_id not in session_memory:
        session_memory[user_id] = []

    session_memory[user_id].append(f"User: {user_input}")
    prompt = "\n".join(session_memory[user_id]) + "\nAssistant:"

    try:
        hf_response = requests.post(
            HUGGINGFACE_API_URL,
            headers=HF_HEADERS,
            json={"inputs": prompt}
        )

        if hf_response.status_code == 200:
            generated = hf_response.json()[0]["generated_text"].split("Assistant:")[-1].strip()
            if generated:
                session_memory[user_id].append(f"Assistant: {generated}")
                return jsonify({"answer": generated})

        raise Exception("Empty or invalid response from Hugging Face")

    except Exception as e:
        try:
            gemini_response = requests.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                headers=GEMINI_HEADERS,
                json={"contents": [{"parts": [{"text": user_input}]}]}
            )
            result = gemini_response.json()
            generated = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            session_memory[user_id].append(f"Assistant: {generated}")
            return jsonify({"answer": generated})
        except:
            fallback_msg = {
                "en": "Sorry, I'm having trouble answering right now. Please try again later.",
                "ar": "عذراً، هناك مشكلة مؤقتة. حاول مرة أخرى لاحقاً."
            }
            return jsonify({"answer": fallback_msg.get(lang, fallback_msg["en"])}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))







