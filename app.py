import os
import json
from datetime import datetime
import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

# 🔥 Import your RAG functions

from backend.rag import search_docs, load_pdf, load_vectorstore

load_dotenv()

# 🔐 API setup

api_key = os.getenv("GROQ_API_KEY")

client = None
if api_key:
    client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
    )
else:
    print("⚠️ API key missing")

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
        json.dump(data, f)

# 📄 Upload PDF

def upload_pdf(file):
    if file is None:
        return "Upload a file first"

    os.makedirs("backend/pdfs", exist_ok=True)
    path = f"backend/pdfs/{file.name}"

    with open(path, "wb") as f:
        f.write(file.read())

    try:
        load_pdf(path)
    except Exception as e:
        return f"Error: {e}"

    return "PDF uploaded ✅"

```
os.makedirs("backend/pdfs", exist_ok=True)
path = f"backend/pdfs/{file.name}"

with open(path, "wb") as f:
    f.write(file.read())

try:
    load_pdf(path)
except Exception as e:
    return f"Error: {e}"

return "PDF uploaded ✅"
```

# 💬 Chat

def chat(user_message):
    if not client:
        return "API key missing"

    try:
        load_vectorstore()
        docs = search_docs(user_message)
        context = "\n\n".join([d.page_content for d in docs]) if docs else ""
    except Exception as e:
        print("RAG error:", e)
        context = ""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Answer based on context"},
                {"role": "user", "content": f"{user_message}\n\nContext:\n{context}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

```
try:
    load_vectorstore()
    docs = search_docs(user_message)
    context = "\n\n".join([d.page_content for d in docs]) if docs else ""
except Exception as e:
    print("RAG error:", e)
    context = ""

try:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Answer based on context"},
            {"role": "user", "content": f"{user_message}\n\nContext:\n{context}"}
        ]
    )
    return response.choices[0].message.content
except Exception as e:
    return f"Error: {e}"
```

# 🎨 UI

with gr.Blocks() as demo:
    gr.Markdown("# 🤖 AI PDF Chatbot")

    file = gr.File(label="Upload PDF")
    upload_btn = gr.Button("Upload PDF")
    output = gr.Textbox()

    upload_btn.click(upload_pdf, inputs=file, outputs=output)

    chatbot = gr.Chatbot()
    msg = gr.Textbox(label="Ask something")

    def respond(message, history):
        reply = chat(message)
        history.append((message, reply))
        return "", history

    msg.submit(respond, [msg, chatbot], [msg, chatbot])

```
file = gr.File(label="Upload PDF")
upload_btn = gr.Button("Upload PDF")
output = gr.Textbox()

upload_btn.click(upload_pdf, inputs=file, outputs=output)

chatbot = gr.Chatbot()
msg = gr.Textbox(label="Ask something")

def respond(message, history):
    reply = chat(message)
    history.append((message, reply))
    return "", history

msg.submit(respond, [msg, chatbot], [msg, chatbot])
```

demo.launch()
