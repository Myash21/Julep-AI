from julep import Julep
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize the client
client = Julep(api_key = os.environ["JULEP_API_KEY"])

user = client.users.create(name = "Yash", about = "Tech enthusisast")

agent = client.agents.create(
    name="Research Assistant",
    model="llama-3.1-70b",  # or any supported model
    about="A helpful research assistant that can search and summarize information.",
    instructions=["Keep your responses concise and to the point.", "If you don't know the answer, say 'I don't know'"],
    metadata={
        "expertise": "research",
        "language": "english"
    }
)


session = client.sessions.create(
    agent = agent.id,
    user = user.id,
    context_overflow="adaptive"
)
print("Agent ID:", agent.id)
print("Session ID:", session.id)

res = client.sessions.chat(
    session_id = session.id,
    messages = [{"content": "Tell me about machine learning", "role":"user"}],
)

print("Agent's response:", res.choices[0].message.content)