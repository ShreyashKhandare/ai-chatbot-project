import os
import json
from datetime import datetime
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# 🔥 SAFE IMPORT
def search_docs(x): return []
def load_pdf(x): pass
def load_vectorstore(): pass

load_dotenv()

app = FastAPI()

# ✅ IMPORTANT ROOT ROUTE (for Render)
@app.get("/")
def home():
    return {"status": "Backend running 🚀"}

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 SAFE API KEY
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("⚠️ GROQ_API_KEY missing!")

client = OpenAI(
    api_key=api_key,
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
    print("App started successfully")

# 🔥 Upload PDF
@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    path = f"pdfs/{file.filename}"

    with open(path, "wb") as f:
        f.write(await file.read())

    try:
        load_pdf(path)
    except Exception as e:
        print("PDF load error:", e)

    return {"message": "PDF uploaded and processed"}

@app.post("/chat")
def chat(req: ChatRequest):

    user_message = req.message
    session_id = req.session_id
    is_voice = req.is_voice

    # 🔥 LOAD VECTORSTORE HERE (SAFE)
    try:
        load_vectorstore()
    except Exception as e:
        print("Vectorstore load error:", e)

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
        load_vectorstore()  # load only when needed
        docs_list = search_docs(user_message)
        docs = "\n\n".join([doc.page_content for doc in docs_list])
    except Exception as e:
        print("Vector error:", e)
        docs = ""

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
        {"role": "user", "content": f"{user_message}\n\nContext:\n{docs}"}
    ]

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

        chat_sessions[session_id].append({
            "role": "user",
            "content": user_message
        })

        chat_sessions[session_id].append({
            "role": "assistant",
            "content": ai_message
        })

        # 🔥 Save name only
        if "my name is" in user_message.lower():
            name = user_message.split("my name is")[-1].strip()
            try:
                memory = load_memory()
                memory[session_id] = f"User name: {name}"
                save_memory(memory)
            except Exception as e:
                print("Memory error:", e)

    return StreamingResponse(generate(), media_type="text/plain")