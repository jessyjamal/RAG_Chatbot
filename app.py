from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask, request, jsonify
import google.generativeai as genai

# Configure Gemini API key from environment variable
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-pro")

app = Flask(__name__)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("question", "")
    try:
        response = model.generate_content(user_input)
        return jsonify({"answer": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
