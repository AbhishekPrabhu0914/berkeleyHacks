# agents/swe_agent.py

from ai_client import call_gemini

class SWEAgent:
    def __init__(self):
        self.last_code = ""

    def implement(self, instructions: str, requirements: str) -> str:
        prompt = f"""
You are a Software Engineer. Based on the following product requirements and PM instructions, write code using the specified tech stack.

📄 Requirements:
{requirements}

📩 Instructions from PM:
{instructions}

Write clean, production-level code in one logical block.
"""
        code = call_gemini(prompt)
        self.last_code = code
        return code
