# controllers/agent_loop.py

from user_interaction_agent import UserInteractionAgent
from pm_agent import PMAgent
from swe_agent import SWEAgent

user_agent = UserInteractionAgent()
pm_agent = PMAgent()
swe_agent = SWEAgent()

def run_agent_interaction(user_inputs):
    responses = []

    for user_input in user_inputs:
        response = user_agent.ask_next(user_input)
        responses.append(response)
        if user_agent.completed:
            break

    if not user_agent.completed:
        return responses

    # Now proceed to SWE-PM loop
    final_reqs = user_agent.get_final_requirements()
    pm_agent.receive_requirements(final_reqs)

    # First code attempt
    initial_code = swe_agent.implement("Please implement the full project.", final_reqs)
    pm_feedback = pm_agent.review_code(initial_code)

    # Second attempt (loop can repeat)
    updated_code = swe_agent.implement(pm_feedback, final_reqs)
    final_feedback = pm_agent.review_code(updated_code)

    return {
        "initial_code": initial_code,
        "pm_feedback_1": pm_feedback,
        "updated_code": updated_code,
        "pm_feedback_2": final_feedback
    }
