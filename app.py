import os
from flask import Flask, request, jsonify
import requests
from langdetect import detect

app = Flask(__name__)

# === Gemini setup ===
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

# === Bot prompts ===
SYSTEM_PROMPT = (
    "You are Tofy 🤖, an educational assistant specialized in helping students find and compare private or international universities and colleges in Egypt. "
    "You only answer questions related to private or international universities, including tuition fees, admission requirements, majors, and comparisons. "
    "If a question is out of scope, politely explain that you focus only on private and international institutions."
)

BOT_INTRO = {
    "en": "Hello, I'm Tofy 👋\nI'm here to help you find the best private or international university in Egypt. Ask me anything!",
    "ar": "أهلاً! أنا توفي 🤖\nموجود علشان أساعدك تلاقي أفضل جامعة أو كلية خاصة أو دولية في مصر. اسألني عن أي حاجة!"
}

# === Memory ===
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
        session_memory[user_id] = [{"role": "user", "text": SYSTEM_PROMPT}]

    session_memory[user_id].append({"role": "user", "text": user_input})

    try:
        response = requests.post(
            GEMINI_URL,
            headers={"Content-Type": "application/json"},
            json={"contents": session_memory[user_id]},
            timeout=20
        )
        response.raise_for_status()
        gemini_output = response.json()
        answer = gemini_output["candidates"][0]["content"]["parts"][0]["text"]
        session_memory[user_id].append({"role": "model", "text": answer})
        return jsonify({"answer": answer})

    except Exception as e:
        print("⚠️ Gemini error:", e)
        fallback_msg = {
            "en": "I'm still learning, so I might not have all the answers yet. But I'm improving every day! 😊",
            "ar": "أنا لسه بتعلم، فممكن تكون في حاجات لسه معرفهاش. بس بوعدك إني بحاول أتحسن كل يوم! 😊"
        }
        return jsonify({"answer": fallback_msg.get(lang, fallback_msg["en"])})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
