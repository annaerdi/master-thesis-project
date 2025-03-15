from playbookgen.utils.schema import function_to_schema
from playbookgen.utils.browser_helpers import build_naive_css_selector
from playbookgen.system_message import SYSTEM_MESSAGE
from playwright.sync_api import sync_playwright, Page, ElementHandle
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI
import json
import yaml


load_dotenv()
client = OpenAI()


# -------------------------------------------------------------------------------------
# Playwright/DOM handling
# -------------------------------------------------------------------------------------

# store active browser sessions in a dictionary so each "session_id" can track a page/browser.
browser_sessions = {}


def get_interactive_elements(session_id: str, output_file: str = "elements.json") -> str:
    """
    Collect interactive elements from current page, save to JSON file, and return results.
    Returns JSON string of elements or error message if session doesn't exist.
    """
    if session_id not in browser_sessions:
        return "No active session. Create one with 'visit' command first."

    page = browser_sessions[session_id]
    try:
        elements = page.query_selector_all("a, button, input, textarea, select")
        interactive_elements = []

        for idx, elem in enumerate(elements, start=1):
            css_selector = build_naive_css_selector(elem)
            interactive_elements.append({
                "index": idx,
                "selector": f"css={css_selector}",
                "tag": elem.evaluate("el => el.tagName"),
                "text": elem.inner_text().strip(),
                "type": elem.get_attribute("type"),
                "id": elem.get_attribute("id"),
                "class": elem.get_attribute("class")
            })

        with open(output_file, "w") as f:
            json.dump(interactive_elements, f, indent=2)

        return json.dumps(interactive_elements, indent=2)
    except Exception as e:
        return f"Error collecting elements: {str(e)}"


class PlaybookState:
    """Simple class to hold our Attackmate YAML playbook in memory."""
    def __init__(self):
        self.commands = []

    def add_step(self, step):
        self.commands.append(step)

    def to_yaml(self):
        return yaml.dump({"commands": self.commands}, sort_keys=False)


# Global “playbook” so we can accumulate steps:
playbook_state = PlaybookState()


def add_playbook_step(
        step_type: str,
        seconds: Optional[int] = None,
        cmd: Optional[str] = None,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        text: Optional[str] = None,
        session: Optional[str] = None,
        creates_session: Optional[str] = None,
        screenshot_path: Optional[str] = None
) -> str:
    """
    Add a step to the YAML playbook.

    For a sleep step:
      - Set step_type to "sleep"
      - Provide the 'seconds' parameter

    For a browser action step:
      - step_type is typically "browser"
      - cmd: the action to perform (e.g. "visit", "click", "type", "screenshot", ...)
      - url: e.g. "https://www.example.com"
      - selector: e.g. "a[href='/about']"
      - text: text to type (if cmd=="type")
      - session: existing browser session name
      - creates_session: session name if the step creates a new browser context
      - screenshot_path: file name to save the screenshot

    The function adds the step to the playbook and, if it's a browser step, executes the browser action.
    """
    if step_type == "sleep":
        if seconds is None:
            raise ValueError("The 'seconds' parameter must be provided for a sleep step.")
        step = {
            "type": "sleep",
            "seconds": seconds
        }
        playbook_state.add_step(step)
        return f"Added sleep step to the playbook:\n{yaml.dump(step, sort_keys=False)}"

    # For non-sleep steps (browser actions)
    if cmd is None:
        raise ValueError("The 'cmd' parameter must be provided for a browser step.")

    step = {
        "type": step_type,
        "cmd": cmd,
    }
    if url is not None:
        step["url"] = url
    if selector is not None:
        step["selector"] = selector
    if text is not None:
        step["text"] = text
    if session is not None:
        step["session"] = session
    if creates_session is not None:
        step["creates_session"] = creates_session
    if screenshot_path is not None:
        step["screenshot_path"] = screenshot_path

    playbook_state.add_step(step)
    do_browser_action(step)
    return f"Added step to the playbook:\n{yaml.dump(step, sort_keys=False)}"


def do_browser_action(step_dict):
    """
    Actually perform the step using Playwright so we keep a real DOM in sync for subsequent calls.
    """
    if step_dict.get("type") != "browser":
        return

    cmd = step_dict.get("cmd")
    session = step_dict.get("session")
    creates_session = step_dict.get("creates_session")

    # Start or retrieve the session
    if creates_session:
        # if it 'creates_session', we start a new browser context here
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        browser_sessions[creates_session] = page
        session = creates_session

    if not session or session not in browser_sessions:
        return

    page = browser_sessions.get(session)
    if not page:
        return

    if cmd == "visit":
        url = step_dict["url"]
        page.goto(url)

    elif cmd == "click":
        selector = step_dict.get("selector")
        if selector:
            page.click(selector)

    elif cmd == "type":
        selector = step_dict.get("selector")
        text = step_dict.get("text", "")
        if selector:
            page.fill(selector, text)

    elif cmd == "screenshot":
        screenshot_path = step_dict.get("screenshot_path", "screenshot.png")
        page.screenshot(path=screenshot_path)

    else:
        print("Unknown command:", cmd)


# -------------------------------------------------------------------------------------
# Chat Orchestration
# -------------------------------------------------------------------------------------

# Our tools for the agent to call:
tools = [get_interactive_elements, add_playbook_step]

def execute_tool_call(tool_call, tools_map):
    """Given a tool call from the model, run the corresponding Python function with provided arguments."""
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    print(f"Assistant invoked tool: {name}({args})")
    return tools_map[name](**args)


def run_full_turn(system_message, tools, messages):
    """
    The main conversation loop. The agent can generate JSON tool calls, which we then execute.
    After any tool calls, we feed back the results as 'tool' messages. The loop continues
    until the assistant returns a final message with no more tool calls.
    """
    num_init_messages = len(messages)
    messages = messages.copy()

    while True:
        # Convert python functions into JSON schemas
        tool_schemas = [function_to_schema(tool) for tool in tools]
        tools_map = {tool.__name__: tool for tool in tools}

        # === 1. Get openai completion ===
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_message}] + messages,
            tools=tool_schemas,
        )

        message = response.choices[0].message
        messages.append(message)

        if message.content:  # The "assistant" response to print for the user
            print("Assistant:", message.content)

        if not message.tool_calls:
            # If there are no tool calls, we assume the conversation step is over
            break

        # === 2. handle tool calls ===
        for tool_call in message.tool_calls:
            result = execute_tool_call(tool_call, tools_map)
            # Return the result to the conversation
            result_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            }
            messages.append(result_message)

    return messages[num_init_messages:]


def main():
    messages = []
    while True:
        try:
            user_input = input("User: ")
            if not user_input.strip():
                print("Exiting...")
                break
            messages.append({"role": "user", "content": user_input})
            new_messages = run_full_turn(SYSTEM_MESSAGE, tools, messages)
            messages.extend(new_messages)
            #print("Current Attackmate Playbook:\n", playbook_state.to_yaml())
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()
