from flask import Flask, request, jsonify
from flask_cors import CORS
from letta_client import Letta
from dotenv import load_dotenv
import os
import traceback

# ------------------ Load Environment ------------------

load_dotenv()

letta_api_key = os.getenv("LETTA_API_KEY")
pm_agent_id = os.getenv("PM_AGENT_ID")
swe_agent_id = os.getenv("SWE_AGENT_ID")

if not letta_api_key:
    raise ValueError("LETTA_API_KEY is missing in .env")
if not pm_agent_id or not swe_agent_id:
    raise ValueError("PM_AGENT_ID or SWE_AGENT_ID is missing in .env")

client = Letta(token=letta_api_key)
pm_agent = client.agents.retrieve(pm_agent_id)
swe_agent = client.agents.retrieve(swe_agent_id)

# ------------------ Flask App Setup ------------------

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

PM_SECTIONS_REQUIRED = [
    "Purpose and Functionality",
    "Core Features",
    "User Roles and Permissions",
    "Tech Stack Preferences",
    "Design/UI",
    "APIs or Integrations",
    "Data Models",
    "Target Audience or Use Case",
    "Deployment Preferences",
]

# ------------------ Helper Functions ------------------

def send_to_agent(agent_id: str, message: str) -> str:
    """Send a message to the specified Letta agent."""
    try:
        response = client.agents.messages.create(
            agent_id=agent_id,
            messages=[{"role": "user", "content": message}]
        )
        for msg in response.messages:
            if msg.message_type == "assistant_message":
                return getattr(msg, "content", None) or getattr(msg, "text", "")
        return "❌ No assistant message found."
    except Exception as e:
        traceback.print_exc()
        return f"❌ Agent Error: {str(e)}"

def identify_missing_sections(requirements: str) -> list:
    """Check if any required PM sections are missing from the input."""
    checklist = ", ".join(PM_SECTIONS_REQUIRED)
    prompt = f"""
You are a helpful product manager. A user provided these product requirements:

\"\"\"{requirements}\"\"\"

Check whether the following sections are clearly described:
{checklist}

List any that are missing, or reply "None" if all are present.
Only return section names, separated by commas.
"""
    result = send_to_agent(pm_agent.id, prompt).strip()
    if result.lower() in ["none", "all present", "all sections present"]:
        return []
    return [section.strip() for section in result.split(",") if section.strip()]

def generate_clarification_request(missing_sections: list) -> str:
    return "To proceed, please provide more details on the following sections: " + ", ".join(missing_sections) + "."

def create_pm_spec(requirements: str) -> str:
    """Ask the PM agent to convert user requirements into a detailed spec."""
    prompt = f"""
Given the following user requirements:

\"\"\"{requirements}\"\"\"

Draft a detailed and structured technical spec for an application. Do not repeat the input back to the user. Instead, break it down into:
- Key user-facing pages or screens and what elements each contains
- User interactions or workflows across the app
- Data flow and API endpoints, if needed
- Suggested component or module layout
- Any technical architecture recommendations

Do not ask for approval — assume approval and proceed.
"""
    return send_to_agent(pm_agent.id, prompt)

def generate_code_from_spec(spec: str) -> str:
    """Ask the SWE agent to implement the approved PM spec."""
    prompt = f"""
You are a senior mobile engineer on a product team.

The PM has finalized and approved the following technical spec. Your task is to immediately implement the described features in code.

🛑 Do NOT ask questions.  
🛑 Do NOT summarize or explain.  
✅ Only return valid, production-ready code for a React Native app.  
✅ Wrap your response in code blocks and assume it's being pasted into a real repo.

---

PM Spec:
\"\"\"{spec}\"\"\"
"""
    return send_to_agent(swe_agent.id, prompt)

def validate_and_iterate_until_approved(spec: str) -> dict:
    """Run the PM-SWE feedback loop until the PM approves the implementation."""
    code = generate_code_from_spec(spec)
    round_counter = 1

    while True:
        feedback_prompt = f"""
You are reviewing the following code implementation based on the approved spec.

Approved Spec:
{spec}

Code:
{code}

Provide feedback, suggestions, or reply 'Approved' to finalize.
"""
        feedback = send_to_agent(pm_agent.id, feedback_prompt)

        if any(kw in feedback.lower() for kw in ["approved", "looks good", "satisfied", "final version", "complete", "ready to deploy"]):
            return {
                "status": "satisfied",
                "rounds": round_counter,
                "final_code": code,
                "pm_feedback": feedback
            }

        revision_prompt = f"""
Revise the code according to this PM feedback:

{feedback}

Previous code:
{code}
"""
        code = send_to_agent(swe_agent.id, revision_prompt)
        round_counter += 1

# ------------------ Routes ------------------

@app.route("/chat", methods=["POST"])
def handle_chat():
    try:
        data = request.get_json()
        message = data.get("message", "").strip()
        if not message:
            return jsonify({"error": "No message provided"}), 400

        missing_sections = identify_missing_sections(message)
        if missing_sections:
            clarification = generate_clarification_request(missing_sections)
            return jsonify({"reply": clarification, "missing_sections": missing_sections})

        spec = create_pm_spec(message)
        result = validate_and_iterate_until_approved(spec)

        return jsonify({
            "status": result["status"],
            "rounds": result["rounds"],
            "generated_code": result["final_code"],
            "pm_feedback": result["pm_feedback"]
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/iterate", methods=["POST"])
def handle_iteration():
    try:
        data = request.get_json()
        iteration_type = data.get("type", "")
        context = data.get("context", "")

        if not iteration_type:
            return jsonify({"error": "No iteration type provided"}), 400

        spec = create_pm_spec(context)
        code = generate_code_from_spec(spec)

        return jsonify({
            "pm_reply": spec,
            "generated_code": code
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ------------------ Run Server ------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
