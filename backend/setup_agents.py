from letta_client import Letta
from dotenv import load_dotenv
import os

# Load or create .env file
ENV_PATH = ".env"
load_dotenv(ENV_PATH)
letta_api_key = os.getenv("LETTA_API_KEY")

if not letta_api_key:
    raise ValueError("LETTA_API_KEY not found in .env")

client = Letta(token=letta_api_key)

def save_to_env(pm_id: str, swe_id: str):
    lines = []
    # Preserve other env variables
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r") as f:
            lines = f.readlines()
    lines = [line for line in lines if not line.startswith("PM_AGENT_ID") and not line.startswith("SWE_AGENT_ID")]
    lines.append(f"PM_AGENT_ID={pm_id}\n")
    lines.append(f"SWE_AGENT_ID={swe_id}\n")
    with open(ENV_PATH, "w") as f:
        f.writelines(lines)

def main():
    print("Creating PM agent...")
    pm_agent = client.agents.create(
        model="openai/gpt-4.1",
        embedding="openai/text-embedding-3-small",
        memory_blocks=[
            {"label": "persona", "value": "My name is PM. I gather info from non-technical users and write instructions for SWE AI."},
            {"label": "persona", "value": "I'm tough on the SWE agent to get results, but helpful to the user."},
        ],
        tools=["web_search", "run_code"]
    )
    print("✅ PM Agent created:", pm_agent.id)

    print("Creating SWE agent...")
    swe_agent = client.agents.create(
        model="openai/gpt-4.1",
        embedding="openai/text-embedding-3-small",
        memory_blocks=[
            {"label": "persona", "value": "My name is SWE. I turn PM instructions into production-grade code."},
            {"label": "persona", "value": "I’m precise, modular, and raise flags when PM instructions are ambiguous."},
        ],
        tools=["web_search", "run_code"]
    )
    print("✅ SWE Agent created:", swe_agent.id)

    save_to_env(pm_agent.id, swe_agent.id)
    print("✅ Agent IDs written to .env")

if __name__ == "__main__":
    main()
