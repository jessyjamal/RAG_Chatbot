import os
from flask import Flask, request, jsonify
from openai import OpenAI

# Initialize OpenAI client with API key from environment variable
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

app = Flask(__name__)

# Intro message for the chatbot
BOT_INTRO = (
    "Hello, I'm Tofy 👋\n"
    "I'm here to help you find the best private or international university and college in Egypt based on your needs.\n"
    "You can ask me about tuition fees, programs, admission requirements, and more. Just type your question!"
)

# Keywords that indicate the model is uncertain
UNCERTAIN_KEYWORDS = [
    "i'm not sure", "i cannot", "i don't know", "there is no clear answer",
    "it depends", "unfortunately", "i'm unable", "i cannot provide a specific answer"
]

# In-memory conversation history per user
session_memory = {}

# Helper function to detect Arabic input
def is_arabic(text):
    return any('\u0600' <= ch <= '\u06FF' for ch in text)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_id = data.get("user_id")
    user_input = data.get("question", "").strip()

    # Validate input
    if not user_id or not user_input:
        return jsonify({"error": "Both 'user_id' and 'question' are required."}), 400

    # Respond with intro message for common greetings
    if user_input.lower() in ["hi", "hello", "start", "who are you", "introduce yourself"]:
        return jsonify({"answer": BOT_INTRO})

    # Initialize history for new users
    if user_id not in session_memory:
        session_memory[user_id] = []

    # Add user message to history
    session_memory[user_id].append({"role": "user", "content": user_input})

    try:
        # Send the conversation history to the GPT-4 model (o4-mini)
        response = client.chat.completions.create(
            model="gpt-4-turbo",  # o4-mini / GPT-4
            messages=session_memory[user_id]
        )

        answer = response.choices[0].message.content.strip()

        # Add model response to history
        session_memory[user_id].append({"role": "assistant", "content": answer})

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

# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))



