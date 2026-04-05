import os
import json
from datetime import datetime
import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 🔥 SAFE IMPORTS (replace later with real ones)
def search_docs(x): return []
def load_pdf(x): pass
def load_vectorstore(): pass

load_dotenv()

# 🔐 API
api_key = os.getenv("GROQ_API_KEY")

client = None
if api_key:
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )
else:
    print("⚠️ API key missing!")

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

# 📄 Upload PDF
def upload_pdf(file):
    if file is None:
        return "Upload a file first"

    os.makedirs("pdfs", exist_ok=True)
    path = f"pdfs/{file.name}"

    with open(path, "wb") as f:
        f.write(file.read())

    try:
        load_pdf(path)
    except Exception as e:
        return f"Error: {e}"

    return "PDF uploaded and processed ✅"

# 💬 Chat function
def chat(user_message, session_id="default"):

    if not client:
        return "API key missing"

    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    history = chat_sessions[session_id][-6:]
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 🔍 RAG
    try:
        load_vectorstore()
        docs_list = search_docs(user_message)
        docs = "\n\n".join([str(doc) for doc in docs_list])
    except Exception as e:
        print("Vector error:", e)
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
        {"role": "user", "content": f"{user_message}\n\nContext:\n{docs}"}
    ]

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages
        )

        reply = completion.choices[0].message.content

    except Exception as e:
        return f"Error: {e}"

    # 💾 Save history
    chat_sessions[session_id].append({"role": "user", "content": user_message})
    chat_sessions[session_id].append({"role": "assistant", "content": reply})

    # 🧠 Save name
    if "my name is" in user_message.lower():
        name = user_message.split("my name is")[-1].strip()
        memory = load_memory()
        memory[session_id] = f"User name: {name}"
        save_memory(memory)

    return reply

# 🎨 UI
with gr.Blocks() as demo:
    gr.Markdown("# 🤖 BITTU AI Chatbot")

    file_input = gr.File(label="Upload PDF")
    upload_btn = gr.Button("Upload PDF")
    upload_output = gr.Textbox()

    upload_btn.click(upload_pdf, inputs=file_input, outputs=upload_output)

    chatbot = gr.Chatbot()
    msg = gr.Textbox(label="Ask something")

    def respond(message, chat_history):
        reply = chat(message)
        chat_history.append((message, reply))
        return "", chat_history

    msg.submit(respond, [msg, chatbot], [msg, chatbot])

demo.queue().launch(server_name="0.0.0.0", server_port=7860)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat_api(request: dict):
    message = request.get("message", "")
    response = chat(message)
    return {"response": response}

# Mount Gradio UI inside FastAPI
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)