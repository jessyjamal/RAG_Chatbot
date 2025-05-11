import os
from flask import Flask, request, jsonify, Response, stream_with_context
import requests
from langdetect import detect
import re
import json

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

    session_memory[user_id].append({"role": "user", "content": user_input})

    def generate():
        try:
            with requests.post(
                url=OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://yourapp.com",
                    "X-Title": "TofyChatbot"
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": session_memory[user_id],
                    "stream": True
                },
                stream=True,
                timeout=60
            ) as response:
                collected = ""
                for line in response.iter_lines():
                    if line and line.startswith(b"data: "):
                        payload = line.decode("utf-8").replace("data: ", "")
                        if payload.strip() == "[DONE]":
                            break
                        try:
                            delta = json.loads(payload)
                            chunk = delta["choices"][0]["delta"].get("content", "")
                            collected += chunk
                            yield chunk
                        except Exception:
                            continue

                cleaned = clean_markdown(collected)
                formatted = format_response(cleaned)
                session_memory[user_id].append({"role": "assistant", "content": formatted})

        except Exception as e:
            yield "\n⚠️ حصل خطأ أثناء جلب الرد."

    return Response(stream_with_context(generate()), content_type="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)



