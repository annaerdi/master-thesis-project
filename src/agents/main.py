from function_to_schema import function_to_schema
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
import json
import yaml


load_dotenv()
client = OpenAI()


# -------------------------------------------------------------------------------------
# Playwright/DOM handling
# -------------------------------------------------------------------------------------
from playwright.sync_api import sync_playwright

# We'll store active browser sessions in a dictionary so each "session_id" can track a page/browser.
browser_sessions = {}

def get_dom(session_id: str) -> str:
    """
    Retrieve the DOM (HTML) for the current page in the given session.
    If session does not exist yet, create it and return an empty string or some default.
    """
    if session_id not in browser_sessions:
        # If no session yet, we create a new browser/page, but haven't navigated anywhere yet
        # so there's no "real" DOM yet. decide later how to handle a blank session.
        return "No active page. Please visit a URL first."

    page = browser_sessions[session_id]
    return page.content()


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
        cmd: str,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        text: Optional[str] = None,
        session: Optional[str] = None,
        creates_session: Optional[str] = None,
        screenshot_path: Optional[str] = None
) -> str:
    """
    Add a single step to our Attackmate-style YAML playbook.

    The arguments roughly map to:

    - step_type: "browser" typically
    - cmd: "visit", "click", "type", "screenshot", ...
    - url: e.g. "https://www.example.com"
    - selector: e.g. "a[href='/about']"
    - text: text to type (if cmd=="type")
    - session: session name for an existing browser context
    - creates_session: session name if the step is creating a new session
    - screenshot_path: file name for a screenshot
    """
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

    # Save the step
    playbook_state.add_step(step)

    # Also perform the step in real time with Playwright (so the DOM changes are real).
    do_browser_action(step)

    return f"Added step to the playbook:\n{yaml.dump(step, sort_keys=False)}"


def do_browser_action(step_dict):
    """
    Actually perform the step using Playwright so we keep a real DOM in sync for subsequent get_dom() calls.
    """
    step_type = step_dict.get("type")
    cmd = step_dict.get("cmd")

    # we only handle `type == "browser"` for this example
    if step_type != "browser":
        return

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

    if not session:
        return  # no session to work with

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

# Example system message: instruct the AI to produce single-step Attackmate “browser” commands.
system_message = (
    "You are simulating a user who browses the web. "
    "You can produce YAML-based Attackmate commands (one step at a time). "
    "After each step, call get_dom to see what's on the new page. "
    "Stop producing steps if you have reached the goal. "
)

# Our tools for the agent to call:
tools = [get_dom, add_playbook_step]

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
            model="gpt-4o-mini",  # or another model
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
        user_input = input("User: ")
        if not user_input.strip():
            print("Exiting...")
            break

        messages.append({"role": "user", "content": user_input})

        new_messages = run_full_turn(system_message, tools, messages)
        messages.extend(new_messages)

        # At the end of each turn, if you want to see the entire playbook so far:
        print("Current Attackmate Playbook:\n", playbook_state.to_yaml())


if __name__ == "__main__":
    main()
