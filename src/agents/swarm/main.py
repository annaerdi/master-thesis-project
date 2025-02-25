from playwright.sync_api import sync_playwright
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


def get_clickable_elements(url: str = "") -> str:
    """
    Uses Playwright to load the provided URL and extract clickable and typable elements.
    This function returns a JSON string with two keys:
      - 'clickable': elements like <a> and <button>
      - 'typable': input fields and textareas
    """
    elements_info = {"clickable": [], "typable": []}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")

            # Extract clickable elements (links and buttons)
            clickable_selectors = "a, button"
            clickable_elements = page.query_selector_all(clickable_selectors)
            for el in clickable_elements:
                try:
                    tag = el.evaluate("el => el.tagName")
                    text = el.inner_text().strip()
                    el_id = el.get_attribute("id")
                    aria_label = el.get_attribute("aria-label")
                    elements_info["clickable"].append({
                        "tag": tag,
                        "id": el_id,
                        "aria-label": aria_label,
                        "text": text
                    })
                except Exception:
                    continue

            # Extract typable elements (text inputs, textareas)
            typable_selectors = "input[type='text'], textarea, input:not([type])"
            typable_elements = page.query_selector_all(typable_selectors)
            for el in typable_elements:
                try:
                    tag = el.evaluate("el => el.tagName")
                    placeholder = el.get_attribute("placeholder")
                    el_id = el.get_attribute("id")
                    elements_info["typable"].append({
                        "tag": tag,
                        "id": el_id,
                        "placeholder": placeholder
                    })
                except Exception:
                    continue
            browser.close()
    except Exception as e:
        # In case of errors (bad URL, network issues, etc.), return error info.
        return json.dumps({"error": str(e)}, indent=2)
    print(json.dumps(elements_info, indent=2))
    return json.dumps(elements_info, indent=2)


# Create a single Agent with a dynamic instructions function, plus the get_dom tool:
playbook_agent = Agent(
    name="Playbook Agent",
    instructions=instructions,
    functions=[get_clickable_elements],
)

if __name__ == "__main__":
    # Example "context variables" used by instructions()
    # context_variables = {"user_name": "James"}

    # Starting conversation
    messages = []
    print("Enter your commands for generating a playbook. To exit, type 'exit' or 'quit'.")
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
