export async function POST(req: Request) {
    const body = await req.json();

    const res = await fetch(
        "https://ai-chatbot-backend-h51v.onrender.com/chat",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(body),
        }
    );

    const data = await res.json();

    return new Response(JSON.stringify(data), {
        status: 200,
    });
}