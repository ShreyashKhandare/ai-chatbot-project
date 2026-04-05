export async function POST(req: Request) {
    try {
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

        const text = await res.text(); // 👈 safer than json()

        let data;

        try {
            data = JSON.parse(text);
        } catch (e) {
            return new Response(
                JSON.stringify({
                    error: "Invalid JSON from backend",
                    raw: text,
                }),
                { status: 500 }
            );
        }

        return new Response(JSON.stringify(data), {
            status: 200,
        });

    } catch (error) {
        return new Response(
            JSON.stringify({ error: "Proxy failed", details: String(error) }),
            { status: 500 }
        );
    }
}