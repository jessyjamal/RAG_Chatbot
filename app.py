import os
from flask import Flask, request, jsonify
import google.generativeai as genai

# Configure Gemini API key from environment variable
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

model = genai.GenerativeModel("models/gemini-1.5-pro")

app = Flask(__name__)

BOT_INTRO = (
    "Hello, I'm Tofy 👋\n"
    "I'm here to help you find the best private or international university and college in Egypt based on your needs.\n"
    "You can ask me about tuition fees, programs, admission requirements, and more. Just type your question!"
)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("question", "").strip().lower()


    if user_input in ["hi", "hello", "start", "who are you", "introduce yourself"]:
        return jsonify({"answer": BOT_INTRO})


    prompt = f"""
You are Tofy, an AI assistant designed to help students choose the best private or international university or college in Egypt.
Only answer questions related to private or international universities, such as tuition fees, majors, admissions, or comparisons.
If a user asks anything outside this scope, respond politely with:
"I'm Tofy I here to help you with private or international university-related questions only. Please ask something within that topic."

Student's question: {user_input}
"""

    try:
        response = model.generate_content(prompt)
        return jsonify({"answer": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

