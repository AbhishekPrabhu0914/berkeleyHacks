import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

def call_gemini(prompt: str) -> str:
    print("[ai_client] Sending prompt:", prompt)
    client = genai.Client(api_key=API_KEY)
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt]
        )
        print("[ai_client] Got response from Gemini")
        return response.text.strip()
    except Exception as e:
        print("[ai_client] Gemini API error:", e)
        return ""

def swe_agent_implement():
    print("[swe_agent] Implementing simple function...")
    prompt = (
        "Write a simple Python function named greet() that takes a name as input "
        "and returns a greeting string like 'Hello, <name>!'"
    )
    code = call_gemini(prompt)
    print("[swe_agent] Function implemented:\n", code)
    return code

def pm_agent_review(code: str):
    print("[pm_agent] Reviewing SWE code...")
    prompt = (
        f"Here is a Python function:\n{code}\n"
        "Please review it and provide feedback or improvements."
    )
    feedback = call_gemini(prompt)
    print("[pm_agent] Feedback:\n", feedback)
    return feedback

def run_agent_interaction():
    print("[agent_loop] Starting agent interaction")

    # SWE writes code
    code = swe_agent_implement()

    # PM reviews code
    feedback = pm_agent_review(code)

    print("[agent_loop] Interaction complete")

if __name__ == "__main__":
    run_agent_interaction()
