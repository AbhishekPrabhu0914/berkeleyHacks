from flask import Flask, request, jsonify
from flask_cors import CORS
from letta_client import Letta
from dotenv import load_dotenv
import os

# --- Load environment variables ---
load_dotenv()
LETTA_API_KEY = os.getenv("LETTA_API_KEY")

# --- Initialize Flask app ---
app = Flask(__name__)
CORS(app, resources={r"/chat": {"origins": [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]}}, supports_credentials=True)

# --- Initialize Letta client and agent ---
client = Letta(token=LETTA_API_KEY)

agent_state = client.agents.create(
    model="openai/gpt-4.1",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "human",
            "value": "The human's name is Chad. They like vibe coding."
        },
        {
            "label": "persona",
            "value": "My name is Sam, the all-knowing sentient AI."
        }
    ],
    tools=["web_search", "run_code"]
)


# --- Utilities ---

def check_requirements_complete(prompt: str):
    response = client.agents.messages.create(
        agent_id=agent_state.id,
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract only assistant responses
    result = "\n".join([
        msg.text for msg in response.messages
        if msg.message_type == "assistant_message"
    ]).strip()

    if result.lower() in ["none", "all present", "all sections present"]:
        return []

    return [s.strip() for s in result.split(",") if s.strip()]


def generate_missing_sections_question(sections):
    section_list = ", ".join(sections)
    return f"Could you provide more detail about the following sections: {section_list}?"


# --- Flask route ---

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        # First: check for missing requirement sections
        missing_sections = check_requirements_complete(user_message)

        if missing_sections:
            reply = generate_missing_sections_question(missing_sections)
            return jsonify({
                "reply": reply,
                "missing_sections": missing_sections
            }), 200

        # Second: continue normal agent conversation
        response = client.agents.messages.create(
            agent_id=agent_state.id,
            messages=[{"role": "user", "content": user_message}]
        )

        reply = "\n".join([
            msg.text for msg in response.messages
            if msg.message_type == "assistant_message"
        ]).strip()

        return jsonify({"reply": reply}), 200

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"error": str(e)}), 500


# --- Run the app ---
if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5001, debug=True)
