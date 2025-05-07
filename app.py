import os
from flask import Flask, request, jsonify
from openai import OpenAI  # From OpenAI SDK v1

# Setup GitHub AI Model (o4-mini or gpt-4o)
client = OpenAI(
    base_url="https://models.github.ai/inference",  # GitHub model inference URL
    api_key=os.environ.get("GITHUB_TOKEN")  # Set your GitHub token as an environment variable
)

app = Flask(__name__)

# Bot introduction message
BOT_INTRO = (
    "Hello, I'm Tofy 👋\n"
    "I'm here to help you find the best private or international university and college in Egypt based on your needs.\n"
    "You can ask me about tuition fees, programs, admission requirements, and more. Just type your question!"
)

# Keywords used to detect uncertainty in the model's answer
UNCERTAIN_KEYWORDS = [
    "i'm not sure", "i cannot", "i don't know", "there is no clear answer",
    "it depends", "unfortunately", "i'm unable", "i cannot provide a specific answer"
]

# In-memory session tracking
session_memory = {}

# Check if text contains Arabic characters
def is_arabic(text):
    return any('\u0600' <= ch <= '\u06FF' for ch in text)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_id = data.get("user_id")
    user_input = data.get("question", "").strip()

    if not user_id or not user_input:
        return jsonify({"error": "Both 'user_id' and 'question' are required."}), 400

    # Intro message on greeting or basic questions
    if user_input.lower() in ["hi", "hello", "start", "who are you", "introduce yourself"]:
        return jsonify({"answer": BOT_INTRO})

    # Create a memory for new users
    if user_id not in session_memory:
        session_memory[user_id] = []

    session_memory[user_id].append({"role": "user", "content": user_input})

    try:
        # Send the message to GitHub's GPT model
        response = client.chat.completions.create(
            model="gpt-4o",  # You can change to "o4-mini" if needed
            messages=session_memory[user_id]
        )

        answer = response.choices[0].message.content.strip()
        session_memory[user_id].append({"role": "assistant", "content": answer})

        # Fallback message if the answer is uncertain
        if any(kw in answer.lower() for kw in UNCERTAIN_KEYWORDS):
            fallback_msg = (
                "I'm still learning, so I'm not completely sure about that. Please try rephrasing your question or check the official website of the university."
                if not is_arabic(user_input)
                else "لسه بتعلم، فمش متأكد من الإجابة دي. جرّب تعيد صياغة سؤالك أو شوف موقع الجامعة الرسمي."
            )
            return jsonify({"answer": fallback_msg})

        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


