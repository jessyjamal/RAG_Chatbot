import os
from flask import Flask, request, jsonify
from openai import OpenAI

# Initialize GitHub Marketplace LLM (o4-mini)
client = OpenAI(
    base_url="https://api.github.ai/v1",  # GitHub Models endpoint
    api_key=os.environ.get("GITHUB_TOKEN"),  # Set this token in environment variables
    default_headers={
        "OpenAI-Organization": "github-models",
        "publisher": "azure-openai"
    }
)

app = Flask(__name__)

# Bot introduction message
BOT_INTRO = (
    "Hello, I'm Tofy 👋\n"
    "I'm here to help you find the best private or international university and college in Egypt based on your needs.\n"
    "You can ask me about tuition fees, programs, admission requirements, and more. Just type your question!"
)

# List of uncertain response indicators
UNCERTAIN_KEYWORDS = [
    "i'm not sure", "i cannot", "i don't know", "there is no clear answer",
    "it depends", "unfortunately", "i'm unable", "i cannot provide a specific answer"
]

# In-memory session per user
session_memory = {}

# Check if the message is Arabic
def is_arabic(text):
    return any('\u0600' <= ch <= '\u06FF' for ch in text)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_id = data.get("user_id")
    user_input = data.get("question", "").strip()

    if not user_id or not user_input:
        return jsonify({"error": "Both 'user_id' and 'question' are required."}), 400

    if user_input.lower() in ["hi", "hello", "start", "who are you", "introduce yourself"]:
        return jsonify({"answer": BOT_INTRO})

    # Initialize session history
    if user_id not in session_memory:
        session_memory[user_id] = []

    session_memory[user_id].append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model="o4-mini",  # Make sure this matches your GitHub Marketplace model name
            messages=session_memory[user_id]
        )

        answer = response.choices[0].message.content.strip()
        session_memory[user_id].append({"role": "assistant", "content": answer})

        if any(keyword in answer.lower() for keyword in UNCERTAIN_KEYWORDS):
            fallback_msg = (
                "لسه بتعلم، فمش متأكد من الإجابة دي. جرّب تعيد صياغة سؤالك أو شوف موقع الجامعة الرسمي."
                if is_arabic(user_input)
                else "I'm still learning, so I'm not completely sure about that. Please try rephrasing your question or check the official university website."
            )
            return jsonify({"answer": fallback_msg})

        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
