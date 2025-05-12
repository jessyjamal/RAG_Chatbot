import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
from langdetect import detect
import re

app = FastAPI()

# === OpenRouter setup ===
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "deepseek/deepseek-chat:free"

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

class ChatRequest(BaseModel):
    user_id: str
    question: str

def clean_markdown(text):
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`{1,3}(.*?)`{1,3}", r"\1", text)
    text = re.sub(r"#+ ", "", text)
    text = re.sub(r"[-•>]", "", text)
    return text.strip()

def format_response(response):
    formatted_response = response.replace("\u2022", "\n\n")
    formatted_response = re.sub(r"\n+", "\n\n", formatted_response)
    return formatted_response.strip()

@app.post("/chat")
async def chat(request: ChatRequest):
    user_id = request.user_id
    user_input = request.question.strip()

    if not user_id or not user_input:
        return JSONResponse(status_code=400, content={"error": "Both 'user_id' and 'question' are required."})

    try:
        lang = detect(user_input)
    except:
        lang = "en"

    if user_input.lower() in [
        "hi", "hello", "start", "who are you", "introduce yourself", "ابدأ", "مرحبا",
        "من أنت", "ازيك", "هاي", "توفي", "هاي توفي"]:
        return {"answer": BOT_INTRO.get(lang, BOT_INTRO["en"])}

    if user_id not in session_memory:
        if lang == "ar":
            system_prompt = (
                "أنت توفي 🤖، مساعد ذكي متخصص في تقديم المساعدة للطلاب بشأن الجامعات والكليات الخاصة والدولية في مصر، "
                "بما في ذلك المصروفات، التخصصات، وشروط القبول. أجب دائمًا باللغة العربية فقط."
            )
        else:
            system_prompt = SYSTEM_PROMPT

        session_memory[user_id] = [{"role": "system", "content": system_prompt}]

    session_memory[user_id].append({"role": "user", "content": user_input})

    try:
        response = requests.post(
            url=OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://yourapp.com",
                "X-Title": "TofyChatbot"
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

        cleaned_answer = clean_markdown(answer)
        formatted_answer = format_response(cleaned_answer)

        session_memory[user_id].append({"role": "assistant", "content": formatted_answer})
        return {"answer": formatted_answer}

    except Exception as e:
        print("\u26a0\ufe0f OpenRouter Error:", str(e))
        fallback_msg = {
            "en": "I'm still learning, so I might not have all the answers yet. But I'm improving every day! 😊",
            "ar": "أنا لسه بتعلم، فممكن تكون في حاجات لسه معرفهاش. بس بوعدك إني بحاول أتحسن كل يوم! 😊"
        }
        return {"answer": fallback_msg.get(lang, fallback_msg["en"])}



