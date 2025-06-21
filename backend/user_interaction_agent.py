# agents/user_interaction_agent.py

from pm_agent import PMAgent
from swe_agent import SWEAgent


class UserInteractionAgent:
    def __init__(self):
        self.pm_agent = PMAgent()
        self.swe_agent = SWEAgent()

    def is_pm_satisfied(self, feedback: str) -> bool:
        """Returns True only if feedback is positive and does NOT contain any critical issues."""
        positive_keywords = [
            "looks good", "approved", "complete", "no changes", "meets all requirements",
            "no further suggestions", "final version", "ready to deploy", "satisfied"
        ]
        critical_keywords = [
            "critical", "must fix", "highest priority", "blocker", "needs to be addressed",
            "missing feature", "fundamental issue", "not acceptable", "refactor required"
        ]

        feedback_lower = feedback.lower()

        has_positive = any(kw in feedback_lower for kw in positive_keywords)
        has_critical = any(kw in feedback_lower for kw in critical_keywords)

        return has_positive and not has_critical

    def run_cli_interaction(self):
        print("📝 Please enter product requirements. Type 'done' when finished:\n")
        collected_input = []

        # 1. Collect requirements
        while True:
            user_input = input(">> ")
            if user_input.lower().strip() == "done":
                requirements = "\n".join(collected_input)
                self.pm_agent.receive_requirements(requirements)

                result = self.pm_agent.handle_requirements_and_review(code="")
                if result["need_more_info"]:
                    print(f"[pm_agent] Missing info: {result['question']}")
                    continue  # Ask for more input
                else:
                    break
            else:
                collected_input.append(user_input)

        print("\n✅ Requirements complete. Generating initial code...")

        # 2. SWE implements code
        instructions = "Please implement the initial code based on the product description."
        code = self.swe_agent.implement(instructions=instructions, requirements=self.pm_agent.requirements)
        print("\n🧠 Initial Code:\n")
        print(code)

        # 3. PM reviews and loop until satisfied
        round_num = 1
        while True:
            print(f"\n🔍 PM Review Round {round_num}")
            feedback = self.pm_agent.review_code(code)
            print("\n🗣️ PM Feedback:\n")
            print(feedback)

            if self.is_pm_satisfied(feedback):
                print("\n✅ PM is satisfied with the code. Final version approved.")
                break

            print("\n🔁 SWE is revising the code based on PM feedback...")
            instructions = f"Please revise the code based on the following PM feedback:\n{feedback}"
            code = self.swe_agent.implement(instructions=instructions, requirements=self.pm_agent.requirements)
            print(f"\n🧠 Updated Code after Round {round_num}:\n")
            print(code)

            round_num += 1

        print("\n🎉 Agent interaction complete.\n")
