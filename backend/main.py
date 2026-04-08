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


# 🔥 FORCE CORS (Render fix)
@app.middleware("http")
async def force_cors(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as e:
        return app.response_class(
            content=json.dumps({"response": "Server crash", "error": str(e)}),
            media_type="application/json"
        )

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


# 💬 Chat logic
def generate_reply(user_message, session_id="default", mode="text"):

    chat_sessions[session_id] = []

    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    # =========================
    # 🔥 LONG TERM MEMORY
    # =========================
    memory = load_memory()

    if session_id not in memory:
        memory[session_id] = {
            "facts": [],
            "history": []
        }

    # store user msg
    memory[session_id]["history"].append(user_message)

    # extract facts
    # 🧠 SMART FACT EXTRACTION (STEP 1)

    important_keywords = [
         "name", "age", "goal", "dream", "like", "love",
        "hate", "career", "study", "work"
    ]

    msg = user_message.lower()

    if any(word in msg for word in important_keywords):
        memory[session_id]["facts"].append(user_message)

    if "i like" in msg:
        like = msg.split("i like")[-1].strip()
        memory[session_id]["facts"].append(f"User likes {like}")

    save_memory(memory)

    # =========================
    # 🔍 RAG
    # =========================
    try:
        load_vectorstore()
        docs = search_docs(user_message)
    except Exception as e:
        print("RAG error:", e)
        docs = ""

    # =========================
    # 🧠 MEMORY → PROMPT
    # =========================
    user_data = memory.get(session_id, {})

    facts_list = user_data.get("facts", [])
    history_list = user_data.get("history", [])

    relevant_facts = get_relevant_memory(user_message, facts_list)
    facts = "\n".join(relevant_facts)

    history_text = "\n".join(history_list[-5:])
    style_instruction = (
        "Give a very short answer in 1-2 lines."
        if mode == "voice"
        else "Give a detailed and helpful answer."
    )

    system_prompt = f"""
    You are BITTU AI — a smart personal assistant.

    {style_instruction}

    IMPORTANT:
    - You REMEMBER the user personally
    - Use memory naturally (not robotic)
    - Do NOT repeat memory unless useful
    - Sound human

    User facts:
    {facts}

    Recent conversation:
    {history_text}
    """

    # =========================
    # ✅ CORRECT MESSAGE FORMAT
    # =========================
    valid_history = [
        msg for msg in chat_sessions[session_id][-6:]
        if "role" in msg and "content" in msg
    ]

    messages = [
        {"role": "system", "content": system_prompt},
        *valid_history,
        {"role": "user", "content": user_message}
    ]

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages
        )

        reply = completion.choices[0].message.content if completion.choices else None

        if not reply:
            return "AI did not return a response"

        # =========================
        # 💾 SAVE CHAT SESSION
        # =========================
        chat_sessions[session_id].append({
            "role": "user",
            "content": user_message
        })

        chat_sessions[session_id].append({
            "role": "assistant",
            "content": reply
        })

        # =========================
        # 💾 SAVE MEMORY (STEP 4)
        # =========================
        memory = load_memory()
        memory[session_id]["history"].append(reply)
        save_memory(memory)

        print("USER:", user_message)
        print("RESPONSE:", reply)

        return reply

    except Exception as e:
        print("LLM ERROR:", e)
        return f"Error: {str(e)}"


# 📡 API
@app.post("/chat")
async def chat_api(request: ChatRequest):
    try:
        response = generate_reply(
            request.message,
            request.session_id,
            request.mode
        )

        if not response:
            return {"response": "No response from AI"}

        return {"response": response}

    except Exception as e:
        print("API ERROR:", e)
        return {
            "response": "Backend error occurred",
            "error": str(e)
        }


# 🏠 Health
@app.get("/")
def home():
    return {"status": "Backend is running 🚀"}