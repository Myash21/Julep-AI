from julep import Julep
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize the client
client = Julep(api_key = os.environ.get("JULEP_API_KEY"))

agent = client.agents.create(
    name="Research Assistant",
    model="claude-3.5-sonnet",  # or any supported model
    about="A helpful research assistant that can search and summarize information.",
    instructions=["Keep your responses concise and to the point.", "If you don't know the answer, say 'I don't know'"],
    metadata={
        "expertise": "research",
        "language": "english"
    }
)

user = client.users.create(name = "Yash", about = "Tech enthusisast")

# Associate a tool with the agent
client.agents.tools.create(
        agent_id=agent.id,
        **{
            "name": "arxiv_search",
            "type": "integration",
            "integration": {
              "provider": "arxiv",
              "method" : "search"
            } 
          },
    )

session = client.sessions.create(
    agent = agent.id,
    user = user.id,
    context_overflow="adaptive"
)

res = client.sessions.chat(
    session_id = session.id,
    messages = [{"content": "Hi", "role":"user"}],
)

print("Agent's response:", res.choices[0].message.content)