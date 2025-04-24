from flask import Flask, request, jsonify, session
from flask_session import Session
from julep import AsyncClient
from dotenv import load_dotenv
import os
import asyncio

# Load .env and setup app
load_dotenv()
api_key = os.environ.get("JULEP_API_KEY")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

client = AsyncClient(api_key=api_key)

# ------------- Utility Functions -------------

async def retrieve_or_create_agent():
    agents = await client.agents.list(metadata_filter={"role": "chatbot"})
    agents_data = [a async for a in agents]

    if not agents_data:
        return await client.agents.create(
            name="Helpful Chatbot",
            about="A helpful assistant that can answer any general user question.",
            default_settings={
                "temperature": 0.7,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "repetition_penalty": 1.0
            },
            model="gpt-4-turbo",
            instructions=["Be helpful, concise, and polite when answering the user's questions."],
            metadata={"role": "chatbot"}
        )
    return agents_data[0]


async def retrieve_or_create_user():
    users = await client.users.list(metadata_filter={"name": "John"})
    users_data = [u async for u in users]

    if not users_data:
        return await client.users.create(
            name="John",
            about="General chatbot user",
            metadata={"name": "John"}
        )
    return users_data[0]


async def retrieve_or_create_session(agent_id, user_id):
    sessions = await client.sessions.list(metadata_filter={
        "agent_id": agent_id,
        "user_id": user_id
    })
    sessions_data = [s async for s in sessions]

    if not sessions_data:
        print("[!] Creating a new session")
        session = await client.sessions.create(
            agent=agent_id,
            user=user_id,
            context_overflow="adaptive"
        )
        return session
    return sessions_data[0]


# ------------- API Routes -------------

@app.route('/start', methods=['POST'])
def start_chat():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    agent = loop.run_until_complete(retrieve_or_create_agent())
    user = loop.run_until_complete(retrieve_or_create_user())
    session_obj = loop.run_until_complete(retrieve_or_create_session(agent.id, user.id))

    session["agent_id"] = agent.id
    session["user_id"] = user.id
    session["session_id"] = session_obj.id

    return jsonify({"message": "Chatbot session started. Ask me anything!"})


@app.route('/ask', methods=['POST'])
def ask_bot():
    if "session_id" not in session:
        return jsonify({"error": "Session not started. Please hit /start first."}), 400

    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)


    response = loop.run_until_complete(client.sessions.chat(
        session_id=session["session_id"],
        messages=[{"content": user_input, "role": "user"}],
        recall=True,
        max_tokens=1000,
    ))

    # ✅ Corrected response parsing
    bot_reply = response.choices[0].message.content
    return jsonify({"response": bot_reply})


# ------------- Main -------------

if __name__ == '__main__':
    app.run(debug=True)
