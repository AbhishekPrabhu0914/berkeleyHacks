# agents/user_interaction_agent.py

from ai_client import call_gemini

class UserInteractionAgent:
    def __init__(self):
        self.prompts = []
        self.completed = False

    def ask_next(self, user_input=None):
        if user_input:
            self.prompts.append(user_input)

        required_sections = [
            "1. Purpose and Functionality",
            "2. Core Features",
            "3. User Roles and Permissions",
            "4. Tech Stack Preferences",
            "5. Design/UI",
            "6. APIs or Integrations",
            "7. Data Models",
            "8. Target Audience or Use Case",
            "9. Deployment Preferences"
        ]

        for idx, section in enumerate(required_sections):
            if len(self.prompts) <= idx:
                return f"Please provide: 🔹 {section}"

        self.completed = True
        return "All requirements collected. Ready to proceed."

    def get_final_requirements(self):
        return "\n".join(self.prompts)
