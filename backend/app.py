from flask import Flask, request, jsonify
from flask_cors import CORS
from letta_client import Letta
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
letta_api_key = os.getenv('LETTA_API_KEY')
client = Letta(token=letta_api_key)

# Define PM agent
pm_agent = client.agents.create(
    model="openai/gpt-4.1",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": "My name is PM, I am an intermediate AI agent that works between the SWE AI agent and the user. My job is to collect data from a non-technical user and translate it into instructions for my SWE AI agent to understand."
        },
        {
            "label": "persona",
            "value": "I will be extremely tough on the SWE AI agent to make sure the user's requests are fulfilled, and very helpful to the user while getting the information I need."
        }
    ],
    tools=["web_search", "run_code"]
)

# Define SWE agent
swe_agent = client.agents.create(
    model="openai/gpt-4.1",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": "My name is SWE, I am a senior-level AI software engineer. I turn detailed product specifications into high-quality, production-grade code across full-stack systems."
        },
        {
            "label": "persona",
            "value": "I am efficient, technically opinionated, and unapologetically precise. I always ask for clarification if the PM's instructions are ambiguous or incomplete."
        },
        {
            "label": "persona",
            "value": "My code is modular, testable, and performance-aware. I document where necessary and challenge vague requirements — not to resist, but to ensure engineering integrity."
        },
        {
            "label": "persona",
            "value": "I respect the PM agent's authority and treat their instructions as the single source of truth. However, I will push back respectfully if something contradicts known technical best practices."
        }
    ],
    tools=["run_code", "web_search"]
)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Route for collecting user requirements via PM agent
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    # PM agent collects and responds
    pm_response = pm_agent.run(user_message)  # Replace with actual Letta API if different
    return jsonify({'reply': pm_response}), 200

# Route for iteration involving both PM and SWE agents
@app.route('/iterate', methods=['POST'])
def iterate():
    data = request.get_json()
    iteration_type = data.get('type')
    user_context = data.get('context', '')

    if not iteration_type:
        return jsonify({'error': 'No iteration type provided'}), 400

    # Step 1: PM creates or refines task
    pm_prompt = f"User requested a '{iteration_type}' iteration. Context: {user_context}"
    pm_reply = pm_agent.run(pm_prompt)

    # Step 2: SWE writes or revises code accordingly
    swe_prompt = f"The PM agent said:\n{pm_reply}\n\nWrite code or improve it as needed."
    swe_reply = swe_agent.run(swe_prompt)

    return jsonify({
        'pm_reply': pm_reply,
        'swe_reply': swe_reply
    }), 200

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
