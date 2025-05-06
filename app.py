import os
from flask import Flask, request, jsonify
import google.generativeai as genai

# Configure Gemini API key
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Create model
model = genai.GenerativeModel("models/gemini-1.5-pro")

# Dictionary to hold chat sessions per user
chat_sessions = {}

app = Flask(__name__)

BOT_INTRO = (
    "Hello, I'm Tofy 👋\n"
    "I'm here to help you find the best private or international university and college in Egypt based on your needs.\n"
    "You can ask me about tuition fees, programs, admission requirements, and more. Just type your question!"
)

DEFAULT_FALLBACK = (
    "I'm not sure about that. Please try rephrasing your question or check the university's official website for more accurate and up-to-date information."
)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    user_id = data.get("user_id")
    user_input = data.get("question", "").strip()

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    if user_input.lower() in ["hi", "hello", "start", "who are you", "introduce yourself"]:
        return jsonify({"answer": BOT_INTRO})

    # Get or create chat session for this user
    if user_id not in chat_sessions:
        chat_sessions[user_id] = model.start_chat(history=[])

    # Better prompt with clearer instructions
    prompt = f"""
You are Tofy, an expert AI assistant who helps students choose the best private or international university or college in Egypt.

Your answers must be:
- Specific, clear, and accurate
- Based on tuition fees, programs, accepted diplomas, admission requirements, locations, or comparisons
- Relevant only to private or international universities in Egypt

If the question is not related to that, reply with:
"I'm Tofy and I can only help with questions about private or international universities in Egypt."

If you do not know the answer for sure, reply with:
{DEFAULT_FALLBACK}

Now respond to the student's question:
{user_input}
"""

    try:
        response = chat_sessions[user_id].send_message(prompt)
        answer = response.text.strip()

        # Check for generic/unsure replies from the model
        if any(keyword in answer.lower() for keyword in ["i'm not sure", "it depends", "i cannot", "i don't have"]):
            return jsonify({"answer": DEFAULT_FALLBACK})

        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
