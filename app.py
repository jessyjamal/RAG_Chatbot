import os
from flask import Flask, request, jsonify
import google.generativeai as genai

# Configure Gemini API key
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Initialize Gemini model
model = genai.GenerativeModel("models/gemini-1.5-pro")

app = Flask(__name__)

# Bot intro
BOT_INTRO = (
    "Hello, I'm Tofy 👋\n"
    "I'm here to help you find the best private or international university and college in Egypt based on your needs.\n"
    "You can ask me about tuition fees, programs, admission requirements, and more. Just type your question!"
)

# Uncertainty indicators
UNCERTAIN_KEYWORDS = [
    "i'm not sure", "i cannot", "i don't know", "there is no clear answer",
    "it depends", "unfortunately", "i'm unable", "i cannot provide a specific answer"
]

# In-memory session storage for each user
session_memory = {}

# Check if input contains Arabic characters
def is_arabic(text):
    return any('\u0600' <= ch <= '\u06FF' for ch in text)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_id = data.get("user_id")
    user_input = data.get("question", "").strip()

    if not user_id or not user_input:
        return jsonify({"error": "Both 'user_id' and 'question' are required."}), 400

    # Return bot intro for common greetings
    if user_input.lower() in ["hi", "hello", "start", "who are you", "introduce yourself"]:
        return jsonify({"answer": BOT_INTRO})

    # Initialize session history if not exists
    if user_id not in session_memory:
        session_memory[user_id] = []

    # Append user message to history
    session_memory[user_id].append({"role": "user", "parts": [user_input]})

    try:
        # Generate a new chat session with previous history
        chat_session = model.start_chat(history=session_memory[user_id])
        response = chat_session.send_message(user_input)
        answer = response.text.strip()

        # Append assistant response to history
        session_memory[user_id].append({"role": "model", "parts": [answer]})

        # Fallback if the model seems uncertain
        if any(kw in answer.lower() for kw in UNCERTAIN_KEYWORDS):
            fallback_msg = (
                "لسه بتعلم، فمش متأكد من الإجابة دي. جرّب تعيد صياغة سؤالك أو شوف موقع الجامعة الرسمي."
                if is_arabic(user_input)
                else "I'm still learning, so I'm not completely sure about that. Please try rephrasing your question or check the official website of the university."
            )
            return jsonify({"answer": fallback_msg})

        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

