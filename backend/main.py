import os
import json
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from openai import OpenAI

# ✅ RAG
from rag import search_docs, load_vectorstore

load_dotenv()

# 🔐 Groq client
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# 🧠 Memory
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


# 📦 Request model
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


# 🚀 FastAPI app
app = FastAPI()

# 🔥 CORS (IMPORTANT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 HANDLE PREFLIGHT (VERY IMPORTANT)
@app.options("/chat")
@app.options("/chat/")
async def options_chat():
    return JSONResponse(content={})


# 💬 Chat logic
def generate_reply(user_message, session_id="default"):

    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    history = chat_sessions[session_id][-6:]
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 🔍 RAG
    try:
        load_vectorstore()
        docs = search_docs(user_message)
    except Exception as e:
        print("RAG error:", e)
        docs = ""

    # 🧠 Memory
    try:
        memory = load_memory()
        user_memory = memory.get(session_id, "")
    except:
        user_memory = ""

    system_prompt = f"""
You are BITTU AI — a smart, friendly assistant.

User info:
{user_memory}

Time: {current_time}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {
            "role": "user",
            "content": f"{user_message}\n\nContext:\n{docs}"
        }
    ]

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages
        )

        reply = completion.choices[0].message.content

    except Exception as e:
        return f"Error: {str(e)}"

    # 💾 Save history
    chat_sessions[session_id].append(
        {"role": "user", "content": user_message}
    )
    chat_sessions[session_id].append(
        {"role": "assistant", "content": reply}
    )

    # 🧠 Save name
    if "my name is" in user_message.lower():
        name = user_message.lower().split("my name is")[-1].strip()
        memory = load_memory()
        memory[session_id] = f"User name: {name}"
        save_memory(memory)

    return reply


# 📡 CHAT ENDPOINT (FIXED FOR BOTH ROUTES)
@app.post("/chat")
@app.post("/chat/")
async def chat_api(request: ChatRequest):
    response = generate_reply(request.message, request.session_id)
    return {"response": response}


# 🏠 Health check
@app.get("/")
def home():
    return {"status": "Backend is running 🚀"}