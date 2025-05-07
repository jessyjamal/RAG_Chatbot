import os
from flask import Flask, request, jsonify
import requests
from langdetect import detect

app = Flask(__name__)

# === Hugging Face setup ===
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
HUGGINGFACE_TOKEN = os.environ.get("HF_TOKEN")
HF_HEADERS = {
    "Authorization": f"Bearer {HUGGINGFACE_TOKEN}",
    "Content-Type": "application/json"
}

# === Gemini setup ===
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")  # set this in your environment
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
        session_memory[user_id] = [f"System: {SYSTEM_PROMPT}"]

    session_memory[user_id].append(f"User: {user_input}")
    prompt = "\n".join(session_memory[user_id]) + "\nAssistant:"

    generated = None

    # === Step 1: Hugging Face ===
    try:
        hf_response = requests.post(
            HUGGINGFACE_API_URL,
            headers=HF_HEADERS,
            json={"inputs": prompt},
            timeout=20
        )
        hf_json = hf_response.json()
        hf_output = hf_json[0]["generated_text"]
        if "Assistant:" in hf_output:
            generated = hf_output.split("Assistant:")[-1].strip()
        else:
            generated = hf_output[len(prompt):].strip()

        if not generated or len(generated) < 2:
            raise Exception("Empty response from Hugging Face")

    except Exception as e:
        print("⚠️ HF error:", e)

    # === Step 2: Gemini fallback ===
    if not generated and GEMINI_API_KEY:
        try:
            gemini_response = requests.post(
                GEMINI_URL,
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": user_input}]}]},
                timeout=20
            )
            gemini_json = gemini_response.json()
            generated = gemini_json["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print("⚠️ Gemini error:", e)

    # === Step 3: Final fallback
    if not generated:
        fallback_msg = {
            "en": "I'm still learning, so I might not have all the answers yet. But I'm improving every day! 😊",
            "ar": "أنا لسه بتعلم، فممكن تكون في حاجات لسه معرفهاش. بس بوعدك إني بحاول أتحسن كل يوم! 😊"
        }
        generated = fallback_msg.get(lang, fallback_msg["en"])

    session_memory[user_id].append(f"Assistant: {generated}")
    return jsonify({"answer": generated})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))










