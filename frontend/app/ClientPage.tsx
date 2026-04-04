"use client";

import { Mic } from "lucide-react";
import { useState, useRef, useEffect } from "react";

type Message = {
    role: "user" | "assistant";
    text: string;
};

export default function ClientPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);

    const bottomRef = useRef<HTMLDivElement | null>(null);
    const recognitionRef = useRef<any>(null);

    // 🎤 Voice Start
    const startListening = () => {
        recognitionRef.current?.start();
    };

    // 🔊 Speak
    const speak = (text: string) => {
        if (!("speechSynthesis" in window)) return;
        const utterance = new SpeechSynthesisUtterance(text);
        window.speechSynthesis.speak(utterance);
    };

    // 📩 Send Message (FINAL FIXED)
    const sendMessage = async (message?: string) => {
        const userMessage = message ?? input; // 👈 IMPORTANT CHANGE

        if (!userMessage.trim()) return;

        // 👇 store BEFORE clearing input
        const finalMessage = userMessage;

        setMessages((prev) => [
            ...prev,
            { role: "user", text: finalMessage },
        ]);

        setInput(""); // clear AFTER storing

        try {
            const res = await fetch(
                "https://ownerofski-ai-chatbot.hf.space/run/predict",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        data: [userMessage, []], // ✅ REQUIRED
                    }),
                }
            );

            const data = await res.json();

            // 👇 VERY IMPORTANT
            const botReply = data.data[1][0][1];

            setMessages((prev) => [
                ...prev,
                { role: "assistant", text: reply },
            ]);
        } catch (error) {
            console.error(error);
        }
    };

    let chatHistory = []; // ✅ put this at TOP of your JS file (outside function)

    async function sendMessage() {
        const userMessage = input.value;

        // show user message in UI (you already have this part)
        addMessage(userMessage, "user");

        // 👇 ADD THIS
        chatHistory.push([userMessage, null]);

        const res = await fetch("https://ownerofski-ai-chatbot.hf.space/run/predict_1", {

            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                data: [userMessage, chatHistory], // ✅ IMPORTANT
            }),
        }
        );

        const data = await res.json();

        // 👇 extract reply
        const reply = data.data[1].slice(-1)[0][1];

        // 👇 update history
        chatHistory[chatHistory.length - 1][1] = reply;

        // show bot message in UI
        addMessage(reply, "bot");

        input.value = "";
    }

    // 📜 Auto Scroll
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // 🎤 Speech Recognition
    useEffect(() => {
        const SpeechRecognition =
            (window as any).SpeechRecognition ||
            (window as any).webkitSpeechRecognition;

        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.lang = "en-US";

            recognition.onresult = (event: any) => {
                const transcript = event.results[0][0].transcript;
                sendMessage(transcript);
            };

            recognitionRef.current = recognition;
        }
    }, []);

    return (
        <div className="flex flex-col h-screen max-w-md mx-auto bg-black text-white">

            {/* HEADER */}
            <div className="p-4 text-center text-lg font-semibold bg-gradient-to-r from-pink-500 to-purple-500 bg-clip-text text-transparent">
                BITTU AI
            </div>

            {/* CHAT */}
            <div className="flex-1 overflow-y-auto px-3 py-4 space-y-2">
                {messages.map((msg, i) => (
                    <div
                        key={i}
                        className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"
                            }`}
                    >
                        <div
                            className={`px-4 py-2 rounded-2xl max-w-[75%] text-sm ${msg.role === "user"
                                ? "bg-gradient-to-r from-pink-500 to-purple-500"
                                : "bg-[#1a1a1a]"
                                }`}
                        >
                            {msg.text}
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="text-gray-400 text-sm">
                        AI is typing...
                    </div>
                )}

                <div ref={bottomRef} />
            </div>

            {/* INPUT */}
            <div className="p-3">
                <div className="flex items-center bg-[#1a1a1a] rounded-full px-4 py-2">

                    <input
                        className="flex-1 bg-transparent text-white outline-none"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Send message..."
                        onKeyDown={(e) => {
                            if (e.key === "Enter") sendMessage();
                        }}
                    />

                    {/* 🎤 MIC */}
                    <button
                        onClick={startListening}
                        className="ml-2 text-gray-400 hover:text-white"
                    >
                        <Mic size={20} />
                    </button>

                </div>
            </div>
        </div>
    );
}