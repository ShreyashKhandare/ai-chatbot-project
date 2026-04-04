"use client";

import { Mic } from "lucide-react";
import { useState, useRef, useEffect } from "react";

type Message = {
    role: "user" | "assistant";
    text: string;
};

export default function ClientPage() {
    const isVoiceInput = useRef(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);

    const bottomRef = useRef<HTMLDivElement | null>(null);
    const recognitionRef = useRef<any>(null);
    const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const fileInputRef = useRef<HTMLInputElement | null>(null);
    const sessionId = useRef<string>("guest");

    // ✅ SESSION ID
    useEffect(() => {
        if (typeof window === "undefined") return;

        let stored: string | null = null;

        try {
            stored = window.localStorage.getItem("user_id");
        } catch {
            stored = null;
        }

        if (stored) {
            sessionId.current = stored;
        } else {
            const newId =
                typeof crypto !== "undefined" && crypto.randomUUID
                    ? crypto.randomUUID()
                    : Math.random().toString(36).substring(2);

            sessionId.current = newId;

            try {
                window.localStorage.setItem("user_id", newId);
            } catch { }
        }
    }, []);

    // 🎤 START VOICE
    const startListening = () => {
        isVoiceInput.current = true;
        recognitionRef.current?.start();
    };

    // 🔊 SPEAK RESPONSE
    const speak = (text: string) => {
        if (typeof window === "undefined") return;
        if (!("speechSynthesis" in window)) return;

        const utterance = new window.SpeechSynthesisUtterance(text);
        utterance.lang = "en-US";
        window.speechSynthesis.speak(utterance);
    };

    // 📩 SEND MESSAGE
    const sendMessage = async () => {
        if (!input.trim()) return;

        const userMessage = input;

        setMessages((prev) => [...prev, { role: "user", text: userMessage }]);
        setInput("");
        setLoading(true);

        try {
            const res = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/chat`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ message: userMessage }),
                }
            );

            const data = await res.json();

            const reply = data?.data?.[0] || "No response from AI";

            setMessages((prev) => [
                ...prev,
                { role: "assistant", text: reply },
            ]);

            speak(reply);
        } catch (error) {
            console.error(error);
            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    text: "Something went wrong. Try again.",
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    // 📜 AUTO SCROLL
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // 🎤 SPEECH RECOGNITION
    useEffect(() => {
        if (typeof window !== "undefined") {
            const SpeechRecognition =
                (window as any).SpeechRecognition ||
                (window as any).webkitSpeechRecognition;

            if (SpeechRecognition) {
                const recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.lang = "en-US";

                recognition.onresult = (event: any) => {
                    const transcript = event.results[0][0].transcript;
                    setInput(transcript);

                    setTimeout(() => {
                        sendMessage();
                    }, 300);
                };

                recognitionRef.current = recognition;
            }
        }
    }, []);

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
                        className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"
                            }`}
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

                {loading && (
                    <div className="text-gray-400 text-sm">AI is typing...</div>
                )}

                <div ref={bottomRef} />
            </div>

            {/* INPUT */}
            <div className="p-3 bg-black">
                <div className="flex items-center bg-[#1a1a1a] rounded-full px-4 py-2 border border-gray-700">
                    <input
                        className="flex-1 bg-transparent text-white outline-none placeholder-gray-400"
                        value={input}
                        onChange={(e) => {
                            const value = e.target.value;
                            setInput(value);

                            if (typingTimeoutRef.current) {
                                clearTimeout(typingTimeoutRef.current);
                            }

                            typingTimeoutRef.current = setTimeout(() => {
                                if (value.trim() && !isVoiceInput.current) {
                                    sendMessage();
                                }
                            }, 1500);
                        }}
                        placeholder="Send message..."
                        onKeyDown={(e) => {
                            if (e.key === "Enter") {
                                sendMessage();
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

                    {/* ➕ FILE */}
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="ml-2 text-gray-400 hover:text-white text-lg"
                    >
                        +
                    </button>

                    <input
                        type="file"
                        ref={fileInputRef}
                        className="hidden"
                        onChange={async (e) => {
                            const file = e.target.files?.[0];
                            if (!file) return;

                            const formData = new FormData();
                            formData.append("file", file);

                            await fetch("/api/upload", {
                                method: "POST",
                                body: formData,
                            });

                            alert("PDF uploaded!");
                        }}
                    />
                </div>
            </div>
        </div>
    );
}