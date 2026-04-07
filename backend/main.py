import os
import json
from datetime import datetime
from statistics import mode
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
    mode: str = "text"  


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

    response.headers["Access-Control-Allow-Origin"] = "https://ai-chatbot-project-r348.vercel.app"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


# 💬 Chat logic
def generate_reply(user_message, session_id="default", mode="text"):

    print("API KEY:", os.getenv("GROQ_API_KEY"))

    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    history = chat_sessions[session_id][-6:]
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 🔥 LONG-TERM MEMORY (ADD HERE)

    memory = load_memory()

    if session_id not in memory:
        memory[session_id] = {
            "facts": [],
            "history": []
        }

    # store user message
    memory[session_id]["history"].append(user_message)

    # extract facts
    if "my name is" in user_message.lower():
        name = user_message.lower().split("my name is")[-1].strip()
        memory[session_id]["facts"].append(f"User name is {name}")

    if "i like" in user_message.lower():
        like = user_message.lower().split("i like")[-1].strip()
        memory[session_id]["facts"].append(f"User likes {like}")

    save_memory(memory)

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
        user_data = memory.get(session_id, {"facts": [], "history": []})

        facts = "\n".join(user_data["facts"][-5:])
        recent_history = "\n".join(user_data["history"][-5:])

        system_prompt = f"""
        You are BITTU AI — a smart personal assistant.

        User known facts:
        {facts}

        Recent conversation:
        {recent_history}

        Instructions:
        - If voice mode → give short answers (1-2 lines)
        - If text mode → give detailed answers
        - Personalize responses using memory
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
       

        # 🔥 SAVE AI RESPONSE (STEP 4)
        memory = load_memory()

        if session_id not in memory:
            memory[session_id] = {
                "facts": [],
                "history": []
            }

        memory[session_id]["history"].append(reply)

        save_memory(memory)

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
        response = generate_reply(request.message, request.session_id, request.mode)

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