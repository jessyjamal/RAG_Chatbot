import os
from flask import Flask, request, jsonify
import requests
from langdetect import detect
from deep_translator import GoogleTranslator
import re

app = Flask(__name__)

# === OpenRouter setup ===
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct:free"

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

def clean_markdown(text):
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`{1,3}(.*?)`{1,3}", r"\1", text)
    text = re.sub(r"#+ ", "", text)
    text = re.sub(r"[-•>]", "", text)
    return text.strip()

def format_response(response):
    formatted_response = response.replace("•", "\n\n")
    formatted_response = re.sub(r"\n+", "\n\n", formatted_response)
    return formatted_response.strip()

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

    if user_input.lower() in ["hi", "hello", "start", "who are you", "introduce yourself", "ابدأ", "مرحبا", "من أنت", "ازيك", "هاي", "توفي", "هاي توفي"]:
        return jsonify({"answer": BOT_INTRO.get(lang, BOT_INTRO["en"])})

    if user_id not in session_memory:
        session_memory[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    original_question = user_input

    if lang == "ar":
        try:
            user_input = GoogleTranslator(source='ar', target='en').translate(user_input)
        except:
            pass

    session_memory[user_id].append({"role": "user", "content": user_input})

    try:
        response = requests.post(
            url=OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://yourapp.com",
                "X-Title": "TofyChatbot"
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": session_memory[user_id]
            },
            timeout=20
        )

        response.raise_for_status()
        output = response.json()
        answer = output["choices"][0]["message"]["content"]

        cleaned_answer = clean_markdown(answer)
        formatted_answer = format_response(cleaned_answer)

        if lang == "ar":
            try:
                translated = GoogleTranslator(source='en', target='ar').translate(formatted_answer)
                formatted_answer = translated
            except:
                pass

        session_memory[user_id].append({"role": "assistant", "content": formatted_answer})
        return jsonify({"answer": formatted_answer})

    except Exception as e:
        print("⚠️ OpenRouter Error:", str(e))
        fallback_msg = {
            "en": "I'm still learning, so I might not have all the answers yet. But I'm improving every day! 😊",
            "ar": "أنا لسه بتعلم، فممكن تكون في حاجات لسه معرفهاش. بس بوعدك إني بحاول أتحسن كل يوم! 😊"
        }
        return jsonify({"answer": fallback_msg.get(lang, fallback_msg["en"])})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)

