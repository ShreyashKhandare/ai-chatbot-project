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
    const modeRef = useRef<"text" | "voice">("text");
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

    // 🔥 Typing Effect (NEW)
    const modeRef = useRef<"text" | "voice">("text");

    // 🔥 Typing effect
    const typeMessage = async (text: string) => {
        let current = "";

        for (let i = 0; i < text.length; i++) {
            current += text[i];

            setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                    role: "assistant",
                    text: current,
                };
                return updated;
            });

            await new Promise((res) => setTimeout(res, 15));
        }
    };

    // ✅ FINAL CLEAN FUNCTION
    const sendMessage = async (
        message?: string,
        mode: "text" | "voice" = "text"
    ) => {

        modeRef.current = mode; // 🔥 store mode

        const userMessage = message ?? input;

        if (!userMessage.trim()) return;

        console.log("MODE:", mode);

        // user message
        setMessages((prev) => [
            ...prev,
            { role: "user", text: userMessage },
        ]);

        setInput("");
        setLoading(true);

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    message: userMessage,
                    session_id: "user1",
                    mode: mode, // ✅ correct now
                }),
            });

            const data = await res.json();
            const botReply = data.response || "No response from AI";

            // empty assistant message
            setMessages((prev) => [
                ...prev,
                { role: "assistant", text: "" },
            ]);

            await new Promise((res) => setTimeout(res, 50));

            // typing
            await typeMessage(botReply);

            // 🔊 ONLY for voice
            if (modeRef.current === "voice") {
                speak(botReply);
            }

        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };
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
                sendMessage(transcript, "voice"); // 🔥 voice mode
            };

            recognitionRef.current = recognition;
        }
    }, []);

    return (
        <div className="flex flex-col h-screen max-w-md mx-auto bg-black text-white">

            {/* HEADER */}
            <div className="p-4 text-center text-lg font-bold bg-gradient-to-r from-pink-500 to-purple-500 bg-clip-text text-transparent">
                BITTU AI 🚀
            </div>

            {/* CHAT */}
            <div className="flex-1 overflow-y-auto px-3 py-4 space-y-3">

                {messages.map((msg, i) => (
                    <div
                        key={i}
                        className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                        <div
                            className={`px-4 py-2 rounded-2xl max-w-[75%] text-sm whitespace-pre-wrap ${msg.role === "user"
                                ? "bg-gradient-to-r from-pink-500 to-purple-500"
                                : "bg-[#1a1a1a]"
                                }`}
                        >
                            {msg.text}
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="text-gray-400 text-sm animate-pulse">
                        AI is thinking...
                    </div>
                )}

                <div ref={bottomRef} />
            </div>

            {/* INPUT */}
            <div className="flex items-center bg-[#1a1a1a] rounded-full px-4 py-2 m-2">

                <input
                    className="flex-1 bg-transparent text-white outline-none"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Type a message..."
                    onKeyDown={(e) => {
                        if (e.key === "Enter") {
                            e.preventDefault();
                            sendMessage(undefined, "text");
                        }
                    }}
                />

                {/* SEND */}
                <button
                    onClick={() => sendMessage(undefined, "text")}
                    className="ml-2 text-white bg-pink-500 px-3 py-1 rounded-lg hover:scale-105 transition"
                >
                    Send
                </button>

                {/* MIC */}
                <button
                    onClick={startListening}
                    className="ml-2 text-gray-400 hover:text-white"
                >
                    <Mic size={20} />
                </button>

            </div>
        </div>
    );
}