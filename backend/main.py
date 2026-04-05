import os
import json
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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

# ✅ CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 FORCE HEADERS (Render fix)
@app.middleware("http")
async def force_cors(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as e:
        # 👇 NEVER return empty response
        return app.response_class(
            content=json.dumps({"response": "Server crash", "error": str(e)}),
            media_type="application/json"
        )

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


# 💬 Chat logic
def generate_reply(user_message, session_id="default"):

    print("API KEY:", os.getenv("GROQ_API_KEY"))

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
    print("API KEY:", os.getenv("GROQ_API_KEY"))
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )

    reply = completion.choices[0].message.content if completion.choices else None

    if not reply:
        print("EMPTY RESPONSE FROM LLM")
        return "AI did not return a response"

    # 🔥 DEBUG LOGS
    print("USER:", user_message)
    print("RESPONSE:", reply)

    if not reply:
        return "No response generated"

    return reply

except Exception as e:
    print("LLM ERROR:", e)
    return f"Error: {str(e)}"


# 📡 Chat endpoint
@app.post("/chat")
async def chat_api(request: ChatRequest):
    try:
        response = generate_reply(request.message, request.session_id)

        if not response:
            return {"response": "No response from AI"}

        return {"response": response}

    except Exception as e:
        print("API ERROR:", e)
        return {
            "response": "Backend error occurred",
            "error": str(e)
        }


# 🏠 Health check
@app.get("/")
def home():
    return {"status": "Backend is running 🚀"}