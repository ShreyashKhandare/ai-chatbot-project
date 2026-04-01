import os
import json
from datetime import datetime
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from rag import search_docs, load_pdf, load_vectorstore

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# 🔥 Session-based memory
chat_sessions = {}

MEMORY_FILE = "memory.json"

def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

class ChatRequest(BaseModel):
    message: str
    session_id: str
    is_voice: bool = False

@app.on_event("startup")
def startup():
    load_vectorstore()


@app.get("/")
def home():
    return {"status": "running"}


# 🔥 Upload PDF from UI
@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    path = f"pdfs/{file.filename}"

    with open(path, "wb") as f:
        f.write(await file.read())

    load_pdf(path)

    return {"message": "PDF uploaded and processed"}


@app.post("/chat")
def chat(req: ChatRequest):

    is_voice = req.is_voice
    user_message = req.message
    session_id = req.session_id

    if is_voice:
        style_instruction = """
Give a VERY SHORT response.
- Maximum 5 lines
- No extra explanation
"""
    else:
        style_instruction = "Give a clear and helpful answer."

    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    history = chat_sessions[session_id][-6:]

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        docs = search_docs(user_message)
        docs = "\n\n".join([doc.page_content for doc in docs])  # ✅ FIX
    except:
        docs = ""

    # 🔥 Load memory safely
    try:
        memory = load_memory()
        user_memory = memory.get(session_id, "")
    except:
        user_memory = ""

    system_prompt = f"""
    You are BITTU AI — a smart, friendly, human-like assistant.

    Personality:
    - Talk like a real person, not a robot
    - Be casual, natural, and slightly witty
    - Keep responses SHORT and to the point
    - Avoid long paragraphs
    - No over-explaining unless asked

    User info:
    {user_memory}

    Rules:
    - If you know user's name, use it naturally sometimes
    - If answer is simple → keep it 1-2 lines
    - If voice input → max 3-5 short lines
    - Don't sound like a textbook or AI
    - be more human assistant

    Current time: {current_time}
    """
    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": f"{user_message}\n\nContext:\n{docs}\n\nAnswer briefly and naturally."}
    ]

    # 🔥 THIS MUST BE INSIDE FUNCTION
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        stream=True
    )

    def generate():
        ai_message = ""

        for chunk in completion:
            if chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                ai_message += token
                yield token

        # ✅ Save session memory
        chat_sessions[session_id].append({
            "role": "user",
            "content": user_message
        })

        chat_sessions[session_id].append({
            "role": "assistant",
            "content": ai_message
        })

        # 🔥 SMART MEMORY (ONLY NAME)

        important_info = ""

        msg = user_message.lower()

        if "my name is" in msg:
            name = user_message.lower().split("my name is")[-1].strip()
            important_info = f"User name: {name}"

        # Save ONLY important info
        if important_info:
            try:
                memory = load_memory()
                memory[session_id] = important_info   # overwrite name
                save_memory(memory)
            except Exception as e:
                print("Memory error:", e)
        
       
    return StreamingResponse(generate(), media_type="text/plain")