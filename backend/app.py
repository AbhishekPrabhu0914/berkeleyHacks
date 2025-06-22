from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from letta_client import Letta
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
letta_api_key = os.getenv('LETTA_API_KEY')
client = Letta(token=letta_api_key)

# ------------------ Letta Agent Setup ------------------

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

# ------------------ Flask Setup ------------------

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ------------------ Constants ------------------

PM_REQUIRED_SECTIONS = [
    "Purpose and Functionality",
    "Core Features",
    "User Roles and Permissions",
    "Tech Stack Preferences",
    "Design/UI",
    "APIs or Integrations",
    "Data Models",
    "Target Audience or Use Case",
    "Deployment Preferences"
]

# ------------------ Helper Functions ------------------

def check_requirements_complete(requirements: str) -> list:
    checklist = ", ".join(PM_REQUIRED_SECTIONS)
    prompt = f"""
You are a helpful product manager. A user provided these product requirements:

\"\"\"
{requirements}
\"\"\"

Check whether the following sections are clearly described:
{checklist}

List any that are missing, or reply "None" if all are present.
Only return section names, separated by commas.
"""
    result = pm_agent.run(prompt).strip()
    if result.lower() in ["none", "all present", "all sections present"]:
        return []
    else:
        return [s.strip() for s in result.split(",") if s.strip()]

def generate_missing_sections_question(missing_sections: list) -> str:
    return (
        "To proceed, please provide more details on the following sections: " +
        ", ".join(missing_sections) + "."
    )

def pm_create_instructions(iteration_type: str, context: str) -> str:
    prompt = f"User requested a '{iteration_type}' iteration. Context:\n{context}\n\nAs PM, evaluate this request and provide detailed product development instructions."
    return pm_agent.run(prompt)

def swe_implement_code(pm_instructions: str) -> str:
    prompt = f"The PM agent said:\n{pm_instructions}\n\nWrite code or revise based on those instructions."
    return swe_agent.run(prompt)

# Optional: PM reviews code
def pm_review_code(requirements: str, code: str) -> str:
    prompt = f"""
You are a Product Manager reviewing the following code based on the user's product requirements:

📄 Requirements:
{requirements}

💻 Code:
{code}

🧠 Please evaluate:
- Does the code fulfill the requirements?
- Are there any bugs, missing logic, or tech stack issues?
- Suggest improvements or request changes.

Return clear, direct feedback to the SWE agent.
"""
    return pm_agent.run(prompt)

# ------------------ Routes ------------------

@app.route('/chat', methods=['POST'])
@cross_origin()
def chat():
    data = request.get_json()
    user_message = data.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    missing_sections = check_requirements_complete(user_message)

    if missing_sections:
        clarification_question = generate_missing_sections_question(missing_sections)
        return jsonify({
            'reply': clarification_question,
            'missing_sections': missing_sections
        }), 200

    pm_response = pm_agent.run(user_message)
    return jsonify({'reply': pm_response}), 200

@app.route('/iterate', methods=['POST'])
@cross_origin()
def iterate():
    data = request.get_json()
    iteration_type = data.get('type')
    user_context = data.get('context', '')

    if not iteration_type:
        return jsonify({'error': 'No iteration type provided'}), 400

    # PM generates detailed product instructions
    pm_reply = pm_create_instructions(iteration_type, user_context)

    # SWE generates code based on PM instructions
    swe_reply = swe_implement_code(pm_reply)

    return jsonify({
        'pm_reply': pm_reply,
        'swe_reply': swe_reply
    }), 200

# ------------------ Run App ------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
