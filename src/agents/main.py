from playwright.sync_api import sync_playwright, Page, ElementHandle
from function_to_schema import function_to_schema
from system_message import SYSTEM_MESSAGE
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

# store active browser sessions in a dictionary so each "session_id" can track a page/browser.
browser_sessions = {}

def build_naive_css_selector(element: ElementHandle) -> str:
    return element.evaluate("""
        (el) => {
            function getSelector(node) {
                if (!node || node.nodeType !== Node.ELEMENT_NODE) return '';
                let selector = node.tagName.toLowerCase();
                if (node.id) {
                    selector += '#' + node.id;
                    return selector;
                }
                if (node.className) {
                    const className = node.className.trim().split(' ')[0];
                    if (className) selector += '.' + className;
                }
                const parent = node.parentElement;
                if (!parent) return selector;
                let index = 1;
                let sibling = node.previousElementSibling;
                while (sibling) {
                    if (sibling.tagName === node.tagName) index += 1;
                    sibling = sibling.previousElementSibling;
                }
                selector += ':nth-of-type(' + index + ')';
                return getSelector(parent) + ' > ' + selector;
            }
            return getSelector(el);
        }
    """)


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
    The arguments map to the fields defined for the BrowserExecutor of AttackMate:
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

        new_messages = run_full_turn(SYSTEM_MESSAGE, tools, messages)
        messages.extend(new_messages)

        # At the end of each turn, if you want to see the entire playbook so far:
        print("Current Attackmate Playbook:\n", playbook_state.to_yaml())


if __name__ == "__main__":
    main()
