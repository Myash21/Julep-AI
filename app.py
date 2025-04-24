from flask import Flask, request, jsonify
from julep import Julep
import os
from dotenv import load_dotenv
import yaml
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Julep client
client = Julep(api_key=os.getenv("JULEP_API_KEY"))

# Create agent (once per session)
agent = client.agents.create(
    name="Research Paper Finder",
    model="claude-3.5-sonnet",
    about="An assistant that helps users find relevant research papers using arXiv."
)

# Attach arXiv search tool
client.agents.tools.create(
    agent_id=agent.id,
    name="arxiv_search",
    **yaml.safe_load("""
    type: integration
    integration:
      provider: arxiv
      method: search
    """)
)

# Define and create the task
task_definition = yaml.safe_load("""
name: ArXiv Search
tools:
- name: arxiv_search
  type: integration
  integration:
    provider: arxiv
    method: search
main:
- tool: arxiv_search
  arguments:
    query: $ steps[0].input.query
    max_results: 10
    download_pdf: False
    sort_by: relevance
    sort_order: descending
""")

task = client.tasks.create(agent_id=agent.id, **task_definition)

@app.route("/research", methods=["POST"])
def research():
    try:
        data = request.get_json()
        topic = data.get("topic")
        output_format = data.get("format")

        if not topic or not output_format:
            return jsonify({"error": "Missing 'topic' or 'format'"}), 400

        prompt = f"Topic: {topic}\nFormat: {output_format}"
        execution = client.executions.create(
            task_id=task.id,
            input={"query": prompt}
        )

        # Wait until it completes
        while (result := client.executions.get(execution.id)).status not in ["succeeded", "failed"]:
            time.sleep(1)

        if result.status == "succeeded":
            return jsonify({"result": result.output})
        else:
            return jsonify({"error": "Execution failed", "details": result.error}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
