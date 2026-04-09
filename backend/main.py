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

# 🔐 API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# 🧠 Memory
chat_sessions = {}
MEMORY_FILE = "memory.json"
vectorstore_loaded = False


# ================= MEMORY =================
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}

    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ================= FASTAPI =================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================= SAFE MIDDLEWARE =================
@app.middleware("http")
async def safe_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as e:
        print("🔥 ERROR:", e)
        return app.response_class(
            content=json.dumps({"response": "Server crashed", "error": str(e)}),
            media_type="application/json"
        )

    return response


# ================= REQUEST =================
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    mode: str = "text"


# ================= AI =================
def generate_reply(user_message, session_id="default", mode="text"):
    global vectorstore_loaded

    print("🧑 USER:", user_message)

    # Init session
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    # Load memory
    memory = load_memory()
    if session_id not in memory:
        memory[session_id] = {"history": [], "facts": []}

    memory[session_id]["history"].append(user_message)

    # Load RAG once
    try:
        if not vectorstore_loaded:
            print("📦 Loading vectorstore...")
            load_vectorstore()
            vectorstore_loaded = True

        docs = search_docs(user_message)
    except Exception as e:
        print("⚠️ RAG ERROR:", e)
        docs = ""

    # Context
    facts = "\n".join(memory[session_id]["facts"][-3:])
    history = "\n".join(memory[session_id]["history"][-5:])

    system_prompt = f"""
You are FREE AI.

Give a helpful answer.

User facts:
{facts}

History:
{history}

Docs:
{docs}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        *chat_sessions[session_id][-6:],
        {"role": "user", "content": user_message}
    ]

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            timeout=20
        )

        reply = completion.choices[0].message.content

    except Exception as e:
        print("🔥 AI ERROR:", e)
        return "⚠️ AI server busy"

    # Save chat
    chat_sessions[session_id].append({"role": "user", "content": user_message})
    chat_sessions[session_id].append({"role": "assistant", "content": reply})

    memory[session_id]["history"].append(reply)
    save_memory(memory)

    return reply


# ================= API =================
@app.post("/chat")
async def chat_api(req: ChatRequest):
    return {
        "response": generate_reply(req.message, req.session_id, req.mode)
    }


@app.get("/")
def home():
    return {"status": "Backend running 🚀"}