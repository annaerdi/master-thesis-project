from swarm import Swarm, Agent
from dotenv import load_dotenv
import json
import os

load_dotenv()
client = Swarm()


def instructions(context_variables: dict = None) -> str:
    """
    This function returns the 'system' instructions for the agent.
    It reads the instructions from a system_message.txt file located one folder up.
    """
    context_variables = context_variables or {}  # it's a dictionary if None
    user_name = context_variables.get("user_name", "User")
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "system_message.txt")

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            system_message = file.read().strip()
    except FileNotFoundError:
        system_message = "Error: system_message.txt not found."
    #print(system_message)
    return system_message.replace("{user_name}", user_name)


def get_dom(query: str = "") -> str:
    """
    Placeholder function returning a dummy DOM snippet.
    In real usage, you'd integrate with Playwright or another browser-automation library.
    """
    dummy_dom = {
        "body": {
            "divs": [
                {"id": "main", "buttons": [{"id": "W0wltc", "text": "I agree"}]},
                {"id": "footer", "links": ["Contact", "Privacy"]},
            ]
        }
    }
    return json.dumps(dummy_dom, indent=2)

# Create a single Agent with a dynamic instructions function, plus the get_dom tool:
playbook_agent = Agent(
    name="Playbook Agent",
    instructions=instructions,  # Could also be a static string
    functions=[get_dom],
)

if __name__ == "__main__":
    # Example "context variables" used by instructions()
    # context_variables = {"user_name": "James"}

    # Starting conversation
    messages = []

    while True:
        user_input = input("User: ")
        if user_input.lower() in ("exit", "quit"):
            print("Exiting.")
            break

        # Put the user's message into the conversation history
        messages.append({"role": "user", "content": user_input})

        # Run a single turn of the agent
        response = client.run(
            agent=playbook_agent,
            messages=messages,
            #context_variables=context_variables
        )

        # The updated conversation with the agent's response
        messages = response.messages

        # print the agent's last reply (YAML steps, etc.)
        # for a single-turn response, typically the final message is at [-1]
        print("Agent:", messages[-1]["content"])
