from ai_client import call_gemini

class PMAgent:
    REQUIRED_SECTIONS = [
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

    def __init__(self):
        self.requirements = ""
        self.last_feedback = ""

    def receive_requirements(self, requirements: str):
        self.requirements = requirements

    def check_requirements_complete(self) -> list:
        prompt = f"""
You are a helpful assistant that reviews product requirements text.
The user wants to build a web app with these requirements:

\"\"\"
{self.requirements}
\"\"\"

Please check if enough of the sections are present to start building an app
{', '.join(self.REQUIRED_SECTIONS)}

List the sections that are missing or incomplete, or reply "None" if all are present.
Only list missing section names separated by commas.
Under No Circumstances should you generate any code, leave that all to the SWE_agent.
"""
        response = call_gemini(prompt).strip()

        if response.lower() in ["none", "all present", "all sections present"]:
            return []
        else:
            missing_sections = [s.strip() for s in response.split(",") if s.strip()]
            return missing_sections

    def get_missing_requirements_question(self, missing_sections: list) -> str:
        sections_str = ", ".join(missing_sections)
        question = (
            f"To proceed, please provide more details on the following missing sections: "
            f"{sections_str}. Could you elaborate on these?"
        )
        return question

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

    def handle_requirements_and_review(self, code: str) -> dict:
        """
        This method will:
        - Check if requirements are complete.
        - If incomplete, return need_more_info and a question.
        - Otherwise, review the code and return feedback.
        """
        missing = self.check_requirements_complete()
        if missing:
            question = self.get_missing_requirements_question(missing)
            return {"need_more_info": True, "question": question}
        else:
            feedback = self.review_code(code)
            return {"need_more_info": False, "feedback": feedback}
