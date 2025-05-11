import os
from flask import Flask, request, jsonify
import requests
from langdetect import detect
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
    """Function to clean markdown and unwanted symbols"""
    # Remove markdown formatting
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # **bold**
    text = re.sub(r"\*(.*?)\*", r"\1", text)      # *italic*
    text = re.sub(r"`{1,3}(.*?)`{1,3}", r"\1", text)  # `code`
    text = re.sub(r"#+ ", "", text)  # Remove headers like ### Title
    text = re.sub(r"[-•>]", "", text)  # Remove bullet symbols
    return text.strip()

def format_response(response):
    """Function to format the response by adding line breaks between universities or colleges"""
    # Example: assume response contains bullet points or separators between universities (e.g., '•' or '\n')
    formatted_response = response.replace("•", "\n\n")  # Adding line breaks after each '•'
    formatted_response = re.sub(r"\n+", "\n\n", formatted_response)  # Remove excessive newlines
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

    if user_input.lower() in ["hi", "hello", "start", "who are you", "introduce yourself", "ابدأ", "مرحبا", "من أنت", "ازيك", "هاي", "توفي","هاي توفي"]:
        return jsonify({"answer": BOT_INTRO.get(lang, BOT_INTRO["en"])})

    # Initialize memory if not exists
    if user_id not in session_memory:
        session_memory[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    session_memory[user_id].append({"role": "user", "content": user_input})

    try:
        response = requests.post(
            url=OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://yourapp.com",  # اختياري
                "X-Title": "TofyChatbot"  # اختياري
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

        # Clean the response if it has unwanted formatting
        cleaned_answer = clean_markdown(answer)
        
        # Format the response with line breaks
        formatted_answer = format_response(cleaned_answer)
        
        session_memory[user_id].append({"role": "assistant", "content": formatted_answer})
        return jsonify({"answer": formatted_answer})

    except Exception as e:
        print("⚠️ OpenRouter Error:", str(e))
        if hasattr(e, 'response') and e.response is not None:
            print("📥 Raw response content:", e.response.text)

        fallback_msg = {
            "en": "I'm still learning, so I might not have all the answers yet. But I'm improving every day! 😊",
            "ar": "أنا لسه بتعلم، فممكن تكون في حاجات لسه معرفهاش. بس بوعدك إني بحاول أتحسن كل يوم! 😊"
        }
        return jsonify({"answer": fallback_msg.get(lang, fallback_msg["en"])})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)


