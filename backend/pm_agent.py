# agents/pm_agent.py

from ai_client import call_gemini

class PMAgent:
    def __init__(self):
        self.requirements = ""
        self.last_feedback = ""

    def receive_requirements(self, requirements: str):
        self.requirements = requirements

    def review_code(self, code: str) -> str:
        prompt = f"""
You are a Product Manager. Review the following code based on the user's product requirements:

📄 Requirements:
{self.requirements}

💻 Code:
{code}

🧠 Please evaluate:
- Does the code fulfill the requirements?
- Are there any bugs, missing logic, or tech stack issues?
- Suggest improvements or request changes.

Return clear, direct feedback to the SWE agent.
"""
        feedback = call_gemini(prompt)
        self.last_feedback = feedback
        return feedback
