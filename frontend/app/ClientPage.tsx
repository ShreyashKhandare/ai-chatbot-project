"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Mic, Bot, User } from "lucide-react";

type Message = {
    role: "user" | "assistant";
    text: string;
};

export default function ClientPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef<HTMLDivElement | null>(null);

    // 🚀 SEND MESSAGE
    const sendMessage = async () => {
        if (!input.trim()) return;

        const userMessage = input;

        setMessages((prev) => [...prev, { role: "user", text: userMessage }]);
        setInput("");
        setLoading(true);

        try {
            const res = await fetch("https://ai-chatbot-project-tudo.onrender.com/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    message: userMessage,
                    session_id: "user1",
                }),
            });

            const data = await res.json();
            const botReply = data.response || "No response";

            // typing effect
            let current = "";
            setMessages((prev) => [...prev, { role: "assistant", text: "" }]);

            for (let i = 0; i < botReply.length; i++) {
                current += botReply[i];

                setMessages((prev) => {
                    const updated = [...prev];
                    updated[updated.length - 1] = {
                        role: "assistant",
                        text: current,
                    };
                    return updated;
                });

                await new Promise((res) => setTimeout(res, 10));
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    // 📜 AUTO SCROLL
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    return (
        <div className="flex h-screen bg-[#0f0f0f] text-white">

            {/* 🔥 SIDEBAR */}
            <div className="w-64 bg-[#111] border-r border-gray-800 p-4 hidden md:flex flex-col">
                <h1 className="text-xl font-bold mb-6 bg-gradient-to-r from-pink-500 to-purple-500 bg-clip-text text-transparent">
                    FREE AI 🚀
                </h1>

                <button className="bg-gradient-to-r from-pink-500 to-purple-500 p-2 rounded-lg text-sm hover:opacity-80">
                    + New Chat
                </button>

                <div className="mt-6 text-gray-400 text-sm">
                    (Chat history coming soon)
                </div>
            </div>

            {/* 💬 MAIN CHAT */}
            <div className="flex flex-col flex-1">

                {/* HEADER */}
                <div className="p-4 border-b border-gray-800 text-center font-semibold">
                    Your AI Assistant
                </div>

                {/* MESSAGES */}
                <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">

                    {messages.map((msg, i) => (
                        <div
                            key={i}
                            className={`flex items-start gap-3 ${msg.role === "user" ? "justify-end" : ""
                                }`}
                        >
                            {msg.role === "assistant" && (
                                <div className="bg-purple-600 p-2 rounded-full">
                                    <Bot size={18} />
                                </div>
                            )}

                            <div
                                className={`px-4 py-3 rounded-2xl max-w-[70%] text-sm leading-relaxed ${msg.role === "user"
                                    ? "bg-gradient-to-r from-pink-500 to-purple-500 ml-auto"
                                    : "bg-[#1a1a1a]"
                                    }`}
                            >
                                {msg.text}
                            </div>

                            {msg.role === "user" && (
                                <div className="bg-pink-600 p-2 rounded-full">
                                    <User size={18} />
                                </div>
                            )}
                        </div>
                    ))}

                    {loading && (
                        <div className="text-gray-400 animate-pulse">
                            AI is thinking...
                        </div>
                    )}

                    <div ref={bottomRef} />
                </div>

                {/* INPUT BAR */}
                <div className="p-4 border-t border-gray-800">
                    <div className="flex items-center bg-[#1a1a1a] rounded-xl px-4 py-3 shadow-lg">

                        <input
                            className="flex-1 bg-transparent outline-none text-sm"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Ask anything..."
                            onKeyDown={(e) => {
                                if (e.key === "Enter") sendMessage();
                            }}
                        />

                        <button
                            onClick={sendMessage}
                            className="ml-2 bg-pink-500 p-2 rounded-lg hover:scale-105 transition"
                        >
                            <Send size={16} />
                        </button>

                        <button className="ml-2 bg-purple-600 p-2 rounded-lg hover:scale-105 transition">
                            <Mic size={16} />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}