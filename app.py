import os
from flask import Flask, request, jsonify
from openai import OpenAI

# Load GitHub PAT from environment variables (used on Railway)
client = OpenAI(
    base_url="https://api.github.ai/v1",
    api_key=os.environ.get("GITHUB_TOKEN"),
    default_headers={
        "OpenAI-Organization": "github-models",
        "publisher": "azure-openai"
    }
)


app = Flask(__name__)

# Bot introduction message
BOT_INTRO = (
    "Hello, I'm Tofy \U0001F44B\n"
    "I'm here to help you find the best private or international university and college in Egypt based on your needs.\n"
    "You can ask me about tuition fees, programs, admission requirements, and more. Just type your question!"
)

# Keywords that indicate uncertainty
UNCERTAIN_KEYWORDS = [
    "i'm not sure", "i cannot", "i don't know", "there is no clear answer",
    "it depends", "unfortunately", "i'm unable", "i cannot provide a specific answer"
]

# Memory store for user sessions
session_memory = {}

# Detect if text contains Arabic characters
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

    # Initialize session if it doesn't exist
    if user_id not in session_memory:
        session_memory[user_id] = []

    # Add the user's message
    session_memory[user_id].append({"role": "user", "content": user_input})

    try:
        # Call GitHub-hosted LLM model
        response = client.chat.completions.create(
            model="openai/o4-mini",  # Model format required by GitHub Marketplace
            messages=session_memory[user_id]
        )

        answer = response.choices[0].message.content.strip()

        # Add assistant's reply to session
        session_memory[user_id].append({"role": "assistant", "content": answer})

        # Handle uncertain answers
        if any(keyword in answer.lower() for keyword in UNCERTAIN_KEYWORDS):
            fallback = (
                "\u0644\u0633\u0647 \u0628\u062a\u0639\u0644\u0645\u060c \u0641\u0645\u0634 \u0645\u062a\u0623\u0643\u062f \u0645\u0646 \u0627\u0644\u0625\u062c\u0627\u0628\u0629 \u062f\u064a. \u062c\u0631\u0651\u0628 \u062a\u0639\u064a\u062f \u0635\u064a\u0627\u063a\u0629 \u0633\u0624\u0627\u0644\u0643 \u0623\u0648 \u0634\u0648\u0641 \u0645\u0648\u0642\u0639 \u0627\u0644\u062c\u0627\u0645\u0639\u0629 \u0627\u0644\u0631\u0633\u0645\u064a."
                if is_arabic(user_input)
                else "I'm still learning, so I'm not completely sure about that. Please try rephrasing your question or check the official university website."
            )
            return jsonify({"answer": fallback})

        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": "Connection error. Please check your token or GitHub model availability."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


