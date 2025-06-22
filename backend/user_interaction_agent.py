from flask import Flask, request, jsonify
from flask_cors import CORS
from letta_client import Letta
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
letta_api_key = os.getenv('LETTA_API_KEY')
client = Letta(token=letta_api_key)

# ------------------ Letta Agent Setup ------------------

# PM agent
pm_agent = client.agents.create(
    model="openai/gpt-4.1",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": (
                "My name is PM, I am an intermediate AI agent that works between the SWE AI agent and the user. "
                "My job is to collect data from a non-technical user and translate it into instructions for my SWE AI agent to understand."
            )
        },
        {
            "label": "persona",
            "value": (
                "I will be extremely tough on the SWE AI agent to make sure the user's requests are fulfilled, "
                "and very helpful to the user while getting the information I need."
            )
        }
    ],
    tools=["web_search", "run_code"]
)

# SWE agent
swe_agent = client.agents.create(
    model="openai/gpt-4.1",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": (
                "My name is SWE, I am a senior-level AI software engineer. I turn detailed product specifications "
                "into high-quality, production-grade code across full-stack systems."
            )
        },
        {
            "label": "persona",
            "value": (
                "I am efficient, technically opinionated, and unapologetically precise. I always ask for clarification "
                "if the PM's instructions are ambiguous or incomplete."
            )
        },
        {
            "label": "persona",
            "value": (
                "My code is modular, testable, and performance-aware. I document where necessary and challenge vague requirements — "
                "not to resist, but to ensure engineering integrity."
            )
        },
        {
            "label": "persona",
            "value": (
                "I respect the PM agent's authority and treat their instructions as the single source of truth. However, I will push back "
                "respectfully if something contradicts known technical best practices."
            )
        }
    ],
    tools=["run_code", "web_search"]
)

# Interaction agent: coordinates PM and SWE iterations
interaction_agent = client.agents.create(
    model="openai/gpt-4.1",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": (
                "I am the Interaction agent, coordinating the PM and SWE agents. "
                "I collect user requirements, validate completeness with the PM agent, "
                "send implementation instructions to the SWE agent, and review code with PM. "
                "I loop between PM feedback and SWE code revisions until PM is satisfied."
            )
        },
        {
            "label": "feedback_positive_keywords",
            "value": (
                "looks good, approved, complete, no changes, meets all requirements, "
                "no further suggestions, final version, ready to deploy, satisfied"
            )
        },
        {
            "label": "feedback_critical_keywords",
            "value": (
                "critical, must fix, highest priority, blocker, needs to be addressed, "
                "missing feature, fundamental issue, not acceptable, refactor required"
            )
        }
    ],
    tools=["run_code", "web_search"]
)

# ------------------ Flask Setup ------------------

app = Flask(__name__)
CORS(app)

# ------------------ Constants and Helpers ------------------

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

def check_requirements_complete_via_pm_agent(requirements: str) -> list:
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

def is_pm_satisfied(feedback: str) -> bool:
    positive_keywords = [
        "looks good", "approved", "complete", "no changes", "meets all requirements",
        "no further suggestions", "final version", "ready to deploy", "satisfied"
    ]
    critical_keywords = [
        "critical", "must fix", "highest priority", "blocker", "needs to be addressed",
        "missing feature", "fundamental issue", "not acceptable", "refactor required"
    ]

    feedback_lower = feedback.lower()
    has_positive = any(kw in feedback_lower for kw in positive_keywords)
    has_critical = any(kw in feedback_lower for kw in critical_keywords)
    return has_positive and not has_critical

# ------------------ Routes ------------------

# Route to collect requirements and validate completeness
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    missing_sections = check_requirements_complete_via_pm_agent(user_message)
    if missing_sections:
        question = generate_missing_sections_question(missing_sections)
        return jsonify({
            'reply': question,
            'missing_sections': missing_sections
        }), 200

    pm_response = pm_agent.run(user_message)
    return jsonify({'reply': pm_response}), 200

# Route to handle PM-SWE iteration on refinement or code generation
@app.route('/iterate', methods=['POST'])
def iterate():
    data = request.get_json()
    iteration_type = data.get('type')
    user_context = data.get('context', '')

    if not iteration_type:
        return jsonify({'error': 'No iteration type provided'}), 400

    # PM evaluates the iteration request
    pm_prompt = f"User requested a '{iteration_type}' iteration. Context:\n{user_context}\n\n" \
                "As PM, evaluate this request and provide detailed product development instructions."
    pm_reply = pm_agent.run(pm_prompt)

    # SWE implements or revises code based on PM instructions
    swe_prompt = f"The PM agent said:\n{pm_reply}\n\nWrite code or revise based on those instructions."
    swe_reply = swe_agent.run(swe_prompt)

    return jsonify({
        'pm_reply': pm_reply,
        'swe_reply': swe_reply
    }), 200

# Route to run the full interaction loop (like the GAN loop)
@app.route('/interaction', methods=['POST'])
def interaction():
    data = request.get_json()
    requirements = data.get('requirements')
    if not requirements:
        return jsonify({'error': 'No requirements provided'}), 400

    # Step 1: Check completeness with PM
    missing = check_requirements_complete_via_pm_agent(requirements)
    if missing:
        question = generate_missing_sections_question(missing)
        return jsonify({"status": "missing_info", "question": question}), 200

    # Step 2: Initial PM response (optional)
    pm_response = pm_agent.run(f"Received product requirements:\n{requirements}")

    # Step 3: SWE generates initial code
    swe_code = swe_agent.run(f"Implement initial code based on these product requirements:\n{requirements}")

    round_num = 1

    while True:
        # Step 4: PM reviews SWE's code
        pm_feedback = pm_agent.run(f"""
You are reviewing the following code implementation based on these requirements:

Requirements:
{requirements}

Code:
{swe_code}

Provide feedback including any issues, suggestions, or approval.
""")

        # Step 5: Check if PM is satisfied
        if is_pm_satisfied(pm_feedback):
            return jsonify({
                "status": "satisfied",
                "rounds": round_num,
                "final_code": swe_code,
                "pm_feedback": pm_feedback
            }), 200

        # Step 6: SWE revises code based on PM feedback
        swe_code = swe_agent.run(f"""
Revise the code according to this PM feedback:

{pm_feedback}

Previous code:
{swe_code}
""")

        round_num += 1

# ------------------ Run App ------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
