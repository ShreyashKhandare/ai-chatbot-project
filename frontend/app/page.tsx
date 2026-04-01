"use client"

import { Mic } from "lucide-react"
import { useState, useRef, useEffect } from "react"

type Message = {
  role: "user" | "assistant"
  text: string
}

export default function Home() {

  const isBrowser = typeof window !== "undefined"
  const isVoiceInput = useRef(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const bottomRef = useRef<HTMLDivElement | null>(null)
  const recognitionRef = useRef<any>(null)
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const sessionId = useRef<string>("guest")

  useEffect(() => {
    if (typeof window === "undefined") return

    let stored: string | null = null

    try {
      stored = window.localStorage.getItem("user_id")
    } catch {
      stored = null
    }

    if (stored) {
      sessionId.current = stored
    } else {
      const newId =
        typeof crypto !== "undefined" && crypto.randomUUID
          ? crypto.randomUUID()
          : Math.random().toString(36).substring(2)

      sessionId.current = newId

      try {
        window.localStorage.setItem("user_id", newId)
      } catch { }
    }
  }, [])
  // 🎤 Start Voice
  const startListening = () => {
    isVoiceInput.current = true
    recognitionRef.current?.start()
  }

  // 🔊 Speak AI response
  const speak = (text: string) => {
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = "en-US"
    speechSynthesis.speak(utterance)
  }

  // 📩 Send Message
  const sendMessage = async (customInput?: string) => {

    const userInput = customInput || input

    if (!userInput.trim()) return

    const voiceMode = isVoiceInput.current
    isVoiceInput.current = false

    setInput("")

    const newMessages = [...messages, { role: "user" as const, text: userInput }]

    setMessages([...newMessages, { role: "assistant" as const, text: "" }])

    try {

      const res = await fetch("https://dummy-api.vercel.app/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          message: userInput,
          session_id: sessionId.current,
          is_voice: voiceMode
        })
      })

      const reader = res.body?.getReader()
      if (!reader) return

      const decoder = new TextDecoder()
      let aiMessage = ""

      while (true) {

        const { done, value } = await reader.read()

        if (done) {
          speak(aiMessage)
          break
        }

        aiMessage += decoder.decode(value)

        setMessages((prev) => {
          const updated = [...prev]
          updated[updated.length - 1] = {
            role: "assistant",
            text: aiMessage
          }
          return updated
        })
      }

    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "⚠️ Server error." }
      ])
    }
  }

  // 📜 Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // 🎤 Speech Recognition Setup
  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition =
        (window as any).SpeechRecognition ||
        (window as any).webkitSpeechRecognition

      if (SpeechRecognition) {
        const recognition = new SpeechRecognition()
        recognition.continuous = false
        recognition.lang = "en-US"

        recognition.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript
          setInput(transcript)

          setTimeout(() => {
            sendMessage(transcript)
          }, 300)
        }

        recognitionRef.current = recognition
      }
    }
  }, [])

  return (

    <div className="flex flex-col h-screen max-w-md mx-auto bg-black text-white relative">

      {/* HEADER */}
      <div className="p-4 text-center text-lg font-semibold bg-gradient-to-r from-pink-500 to-purple-500 bg-clip-text text-transparent">
        siri-yes
      </div>

      {/* CHAT AREA */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-2 bg-gradient-to-b from-black via-[#0f0f0f] to-black">

        {messages.map((msg, i) => (

          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >

            <div
              className={`px-4 py-2 rounded-2xl max-w-[75%] text-sm shadow-md ${msg.role === "user"
                ? "bg-gradient-to-r from-pink-500 to-purple-500"
                : "bg-[#1a1a1a] text-gray-200 backdrop-blur-md"
                }`}
            >
              {msg.text}
            </div>

          </div>

        ))}

        <div ref={bottomRef} />

      </div>

      <div className="p-3 bg-black">

        <div className="flex items-center bg-[#1a1a1a] rounded-full px-4 py-2 border border-gray-700">

          {/* INPUT */}
          <input
            className="flex-1 bg-transparent text-white outline-none placeholder-gray-400"
            value={input}
            onChange={(e) => {
              const value = e.target.value
              setInput(value)

              if (typingTimeoutRef.current) {
                clearTimeout(typingTimeoutRef.current)
              }

              typingTimeoutRef.current = setTimeout(() => {
                if (value.trim() && !isVoiceInput.current) {
                  sendMessage(value)
                }
              }, 1500)
            }}
            placeholder="Send message..."
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                sendMessage(input)
              }
            }}
          />

          {/* 🎤 MIC */}
          <button
            onClick={startListening}
            className="ml-2 text-gray-400 hover:text-white"
          >
            <Mic size={20} />
          </button>

          {/* ➕ UPLOAD */}
          <button
            onClick={() => fileInputRef.current?.click()}
            className="ml-2 text-gray-400 hover:text-white text-lg"
          >
            +
          </button>

          {/* HIDDEN FILE INPUT */}
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            onChange={async (e) => {
              const file = e.target.files?.[0]
              if (!file) return

              const formData = new FormData()
              formData.append("file", file)

              await fetch("https://dummy-api.vercel.app/api/upload", {
                method: "POST",
                body: formData
              })

              alert("PDF uploaded!")
            }}
          />

        </div>

      </div>

    </div>
  )
}