from flask import Flask, request, jsonify
from flask_cors import CORS
from letta_client import Letta
from dotenv import load_dotenv
import os
import traceback

# ------------------ Load Env ------------------
load_dotenv()
letta_api_key = os.getenv("LETTA_API_KEY")
client = Letta(token=letta_api_key)

# ------------------ Create Agents Once ------------------
pm_agent = client.agents.create(
    model="openai/gpt-4.1",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": "My name is PM. I gather info from non-technical users and write instructions for SWE AI."
        },
        {
            "label": "persona",
            "value": "I'm tough on the SWE agent to get results, but helpful to the user."
        },
    ],
    tools=["web_search", "run_code"]
)

swe_agent = client.agents.create(
    model="openai/gpt-4.1",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": "My name is SWE. I turn PM instructions into production-grade code."
        },
        {
            "label": "persona",
            "value": "I’m precise, modular, and raise flags when PM instructions are ambiguous."
        },
    ],
    tools=["web_search", "run_code"]
)

# ------------------ Flask Setup ------------------
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

PM_REQUIRED_SECTIONS = [
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
    try:
        print(f"\n🚀️  Sending to agent: {agent_id}")
        print(f"📨 Message: {message}\n")

        result = client.agents.messages.create(
            agent_id=agent_id,
            messages=[{"role": "user", "content": message}]
        )

        print("📬 Raw response from Letta:", result)

        for msg in result.messages:
            if msg.message_type == "assistant_message":
                return msg.content
        return "No assistant message found."
    except Exception as e:
        print("❌ Error while sending to agent:", e)
        traceback.print_exc()
        raise

def check_requirements_complete(requirements: str) -> list:
    checklist = ", ".join(PM_REQUIRED_SECTIONS)
    prompt = f"""
You are a helpful product manager. A user provided these product requirements:

\"\"\"{requirements}\"\"\"

Check whether the following sections are clearly described:
{checklist}

List any that are missing, or reply \"None\" if all are present.
Only return section names, separated by commas.
"""
    result = send_to_agent(pm_agent.id, prompt).strip()
    if result.lower() in ["none", "all present", "all sections present"]:
        return []
    else:
        return [s.strip() for s in result.split(",") if s.strip()]

def generate_missing_sections_question(missing_sections: list) -> str:
    return "To proceed, please provide more details on the following sections: " + ", ".join(missing_sections) + "."

def pm_create_instructions(requirements: str) -> str:
    prompt = f"""
Given the following user requirements:

\"\"\"{requirements}\"\"\"

Draft a detailed and structured technical spec for an application. Do not repeat the input back to the user. Instead, break it down into:
- Key user-facing pages or screens and what elements each contains
- User interactions or workflows across the app
- Data flow and API endpoints, if needed
- Suggested component or module layout
- Any technical architecture recommendations

After the draft, ask the user for approval by replying with either 'Approved' or 'Not Approved'. If 'Not Approved', revise the spec and ask again.
Once approved, notify the SWE agent to begin implementation.
"""
    return send_to_agent(pm_agent.id, prompt)

def swe_implement_code(pm_instructions: str) -> str:
    prompt = f"The PM agent said:\n{pm_instructions}\n\nWrite code or revise based on those instructions."
    return send_to_agent(swe_agent.id, prompt)

# ------------------ Routes ------------------

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message")

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        normalized = user_message.strip().lower()

        # Handle approval
        if normalized == "approved":
            approval_ack = "Thank you for the approval. Notifying SWE to begin implementation."
            swe_reply = swe_implement_code(approval_ack)
            return jsonify({
                "reply": approval_ack,
                "swe_reply": swe_reply
            })

        # Handle rejection
        if normalized == "not approved":
            revision_prompt = "The previous spec was not approved. Please revise the technical specification and ask for approval again."
            revised_spec = send_to_agent(pm_agent.id, revision_prompt)
            return jsonify({
                "reply": revised_spec
            })

        missing_sections = check_requirements_complete(user_message)
        if missing_sections:
            clarification = generate_missing_sections_question(missing_sections)
            return jsonify({
                "reply": clarification,
                "missing_sections": missing_sections
            })

        pm_response = pm_create_instructions(user_message)
        return jsonify({"reply": pm_response})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def iterate():
    try:
        data = request.get_json()
        iteration_type = data.get("type")
        user_context = data.get("context", "")

        if not iteration_type:
            return jsonify({"error": "No iteration type provided"}), 400

        pm_reply = pm_create_instructions(user_context)
        swe_reply = swe_implement_code(pm_reply)

        return jsonify({
            "pm_reply": pm_reply,
            "swe_reply": swe_reply
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ------------------ Run ------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
