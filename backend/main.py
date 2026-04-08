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

# 🔐 Groq client (SAFE INIT)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# 🧠 Memory
chat_sessions = {}
MEMORY_FILE = "memory.json"
vectorstore_loaded = False


def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print("Memory load error:", e)
        return {}


def save_memory(data):
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("Memory save error:", e)


def get_relevant_memory(user_message, facts):
    relevant = []

    for fact in facts:
        if any(word in fact.lower() for word in user_message.lower().split() if len(word) > 2):
            relevant.append(fact)

    return relevant[-3:] if relevant else facts[-3:]


# 📦 Request model
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    mode: str = "text"


# 🚀 FastAPI app
app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 🔥 GLOBAL SAFE MIDDLEWARE (IMPORTANT)
@app.middleware("http")
async def safe_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as e:
        print("🔥 GLOBAL ERROR:", e)
        return app.response_class(
            content=json.dumps({
                "response": "Server crashed",
                "error": str(e)
            }),
            media_type="application/json"
        )

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


# 💬 Chat logic
def generate_reply(user_message, session_id="default", mode="text"):
    try:
        print("\n🧑 USER:", user_message)

        if session_id not in chat_sessions:
            chat_sessions[session_id] = []

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        # ================= MEMORY =================
        try:
            memory = load_memory()
        except Exception as e:
            print("Memory error:", e)
            memory = {}

        if session_id not in memory:
            memory[session_id] = {"facts": [], "history": []}

        memory[session_id]["history"].append(user_message)

        msg = user_message.lower()

        important_keywords = [
            "name", "age", "goal", "dream", "like", "love",
            "hate", "career", "study", "work"
        ]

        if any(word in msg for word in important_keywords):
            memory[session_id]["facts"].append(user_message)

        save_memory(memory)

        # ================= RAG =================
        # ================= RAG =================
        global vectorstore_loaded

        try:
            if not vectorstore_loaded:
                print("Loading vectorstore...")
                load_vectorstore()
                vectorstore_loaded = True

            docs = search_docs(user_message)

        except Exception as e:
            print("⚠️ RAG ERROR:", e)
            docs = ""

        # ================= SAFE MEMORY =================
        user_data = memory.get(session_id, {})

        facts_list = user_data.get("facts", [])
        history_list = user_data.get("history", [])

        relevant_facts = facts_list[-3:]
        facts = "\n".join(relevant_facts)
        history_text = "\n".join(history_list[-5:])

        style_instruction = (
            "Give a very short answer in 1-2 lines."
            if mode == "voice"
            else "Give a detailed and helpful answer."
        )

        system_prompt = f"""
You are FREE AI.

{style_instruction}

User facts:
{facts}

Recent conversation:
{history_text}

Docs:
{docs}

Time: {current_time}
"""

        # ================= MESSAGES =================
        valid_history = [
            msg for msg in chat_sessions[session_id]
            if isinstance(msg, dict) and "role" in msg and "content" in msg
        ]

        messages = [
            {"role": "system", "content": system_prompt},
            *valid_history[-6:],
            {"role": "user", "content": user_message}
        ]

        # ================= LLM (SAFE) =================
        try:
            if not GROQ_API_KEY:
                return "⚠️ API key missing"

            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                timeout=20
            )

            reply = completion.choices[0].message.content

        except Exception as e:
            print("🔥 GROQ ERROR:", e)
            return "⚠️ AI server busy. Try again."

        if not reply:
            return "No response from AI"

        # ================= SAVE CHAT =================
        chat_sessions[session_id].append({
            "role": "user",
            "content": user_message
        })

        chat_sessions[session_id].append({
            "role": "assistant",
            "content": reply
        })

        memory[session_id]["history"].append(reply)
        save_memory(memory)

        print("🤖 AI:", reply)

        return reply

    except Exception as e:
        print("🔥 FULL ERROR:", e)
        return "⚠️ Server error occurred"


# 📡 API
@app.post("/chat")
async def chat_api(request: ChatRequest):
    try:
        response = generate_reply(
            request.message,
            request.session_id,
            request.mode
        )

        return {"response": response or "No response"}

    except Exception as e:
        print("API ERROR:", e)
        return {
            "response": "⚠️ Backend error",
            "error": str(e)
        }


# 🏠 Health
@app.get("/")
def home():
    return {"status": "Backend is running 🚀"}