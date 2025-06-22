from flask import Flask, request, jsonify
from flask_cors import CORS
from letta_client import Letta
from dotenv import load_dotenv
import os
import traceback
from flask import send_file
import zipfile
import io
import re

# ------------------ Load Environment ------------------

load_dotenv()
letta_api_key = os.getenv("LETTA_API_KEY")
pm_agent_id = os.getenv("PM_AGENT_ID")
swe_agent_id = os.getenv("SWE_AGENT_ID")

if not letta_api_key:
    raise ValueError("LETTA_API_KEY is missing in .env")

if not pm_agent_id or not swe_agent_id:
    raise ValueError("PM_AGENT_ID or SWE_AGENT_ID missing in .env")

client = Letta(token=letta_api_key)
pm_agent = client.agents.retrieve(pm_agent_id)
swe_agent = client.agents.retrieve(swe_agent_id)

# ------------------ Flask App ------------------

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
        response = client.agents.messages.create(
            agent_id=agent_id,
            messages=[{"role": "user", "content": message}]
        )
        for msg in response.messages:
            if msg.message_type == "assistant_message":
                return getattr(msg, "content", None) or getattr(msg, "text", "")
        return "No assistant message found."
    except Exception as e:
        traceback.print_exc()
        return f"❌ Agent Error: {e}"

def check_requirements_complete(requirements: str) -> list:
    checklist = ", ".join(PM_REQUIRED_SECTIONS)
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

Do not ask for approval — assume approval and proceed.
"""
    return send_to_agent(pm_agent.id, prompt)

def swe_implement_code(pm_instructions: str) -> str:
    prompt = f"""
You are a senior mobile engineer on a product team.

The PM has finalized and approved the following technical spec. Your task is to immediately implement the described features in code.

🛑 Do NOT ask questions.  
🛑 Do NOT summarize or explain.  
✅ Only return valid, production-ready code for a React Native app.  
✅ Wrap your response in code blocks and assume it's being pasted into a real repo.

---

PM Spec:
\"\"\"{pm_instructions}\"\"\"
"""
    return send_to_agent(swe_agent.id, prompt)

def run_interaction_loop(spec: str) -> dict:
    swe_code = swe_implement_code(spec)
    round_num = 1

    while True:
        pm_feedback = send_to_agent(pm_agent.id, f"""
You are reviewing the following code implementation based on the approved spec.

Approved Spec:
{spec}

Code:
{swe_code}

Provide feedback, suggestions, or reply 'Approved' to finalize.
""")

        if any(keyword in pm_feedback.lower() for keyword in [
            "approved", "looks good", "satisfied", "final version", "complete", "ready to deploy"
        ]):
            return {
                "status": "satisfied",
                "rounds": round_num,
                "final_code": swe_code,
                "pm_feedback": pm_feedback
            }

        swe_code = send_to_agent(swe_agent.id, f"""
Revise the code according to this PM feedback:

{pm_feedback}

Previous code:
{swe_code}
""")
        round_num += 1

# ------------------ Routes ------------------
def extract_files_from_code_output(output: str) -> dict:
    """Parse code blocks from SWE response into {file_path: code}."""
    files = {}
    pattern = r"### File: (.*?)\n```[^\n]*\n(.*?)\n```"
    matches = re.findall(pattern, output, re.DOTALL)
    for path, content in matches:
        files[path.strip()] = content.strip()
    return files

@app.route("/download-zip", methods=["POST"])
def download_zip():
    try:
        data = request.get_json()
        code = data.get("code", "")
        if not code:
            return jsonify({"error": "No code provided"}), 400

        files = extract_files_from_code_output(code)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for path, content in files.items():
                zipf.writestr(path, content)

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name="project.zip"
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        missing_sections = check_requirements_complete(user_message)
        if missing_sections:
            clarification = generate_missing_sections_question(missing_sections)
            return jsonify({"reply": clarification, "missing_sections": missing_sections})

        pm_response = pm_create_instructions(user_message)
        gan_result = run_interaction_loop(pm_response)

        return jsonify({
            "status": gan_result["status"],
            "rounds": gan_result["rounds"],
            "generated_code": gan_result["final_code"],
            "pm_feedback": gan_result["pm_feedback"]
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/iterate", methods=["POST"])
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
            "generated_code": swe_reply
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ------------------ Run ------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
