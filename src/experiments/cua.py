"""
Tutorial from: https://platform.openai.com/docs/guides/tools-computer-use
Run docker container with:
docker run --rm -it --name cua-image -p 5900:5900 -e DISPLAY=:99 cua-image
"""
import os
import time
import base64
import subprocess
import openai
from dotenv import load_dotenv


###############################################################################
# 1) Configure environment and OpenAI credentials
###############################################################################
load_dotenv()

# Adjust to match your container name
DOCKER_CONTAINER_NAME = "cua-image"

# The X display inside the Docker container
DOCKER_DISPLAY = ":99"

###############################################################################
# 2) Helper function to run commands inside Docker
###############################################################################

def docker_exec(cmd: str, decode=True) -> str:
    """
    Executes 'cmd' inside your Docker container and returns stdout.
    """
    safe_cmd = cmd.replace('"', '\\"')
    docker_cmd = f'docker exec {DOCKER_CONTAINER_NAME} sh -c "{safe_cmd}"'
    output = subprocess.check_output(docker_cmd, shell=True)
    if decode:
        return output.decode("utf-8", errors="ignore")
    return output

###############################################################################
# 3) Function to handle model actions in the Docker environment
###############################################################################

def handle_model_action(action):
    """
    Execute a single 'computer_call' action (e.g. click, type, scroll) via xdotool.
    'action' is typically a Pydantic object from openai's library (e.g. ActionClick).
    """
    action_type = action.type

    if action_type == "click":
        x = action.x
        y = action.y
        button_name = action.button
        button_map = {"left": 1, "middle": 2, "right": 3}
        button = button_map.get(button_name, 1)
        print(f"--> Action: click at ({x}, {y}) with button '{button_name}'")
        docker_exec(f'DISPLAY={DOCKER_DISPLAY} xdotool mousemove {x} {y} click {button}')

    elif action_type == "keypress":
        # 'keys' should be a list of strings
        keys = action.keys
        for key in keys:
            print(f"--> Action: keypress '{key}'")
            upper_k = key.upper()
            if upper_k == "ENTER":
                docker_exec(f'DISPLAY={DOCKER_DISPLAY} xdotool key Return')
            elif upper_k == "SPACE":
                docker_exec(f'DISPLAY={DOCKER_DISPLAY} xdotool key space')
            else:
                docker_exec(f'DISPLAY={DOCKER_DISPLAY} xdotool key {key}')

    elif action_type == "type":
        # 'text' should be a string
        text = action.text
        print(f"--> Action: type text '{text}'")
        docker_exec(f'DISPLAY={DOCKER_DISPLAY} xdotool type \'{text}\'')

    elif action_type == "scroll":
        x = action.x
        y = action.y
        scroll_x = action.scrollX
        scroll_y = action.scrollY
        print(f"--> Action: scroll at ({x}, {y}), scrollX={scroll_x}, scrollY={scroll_y}")

        # Move mouse
        docker_exec(f'DISPLAY={DOCKER_DISPLAY} xdotool mousemove {x} {y}')

        # Vertical scroll: xdotool uses button 4=up, 5=down
        if scroll_y != 0:
            button = 4 if scroll_y < 0 else 5
            clicks = abs(scroll_y)
            for _ in range(clicks):
                docker_exec(f'DISPLAY={DOCKER_DISPLAY} xdotool click {button}')

        # Horizontal scrolling is trickier, typically not used in a minimal example

    elif action_type == "wait":
        print("--> Action: wait (2s)")
        time.sleep(2)

    elif action_type == "screenshot":
        print("--> Action: screenshot (no-op here)")

    else:
        print(f"!!! Unrecognized action type: '{action_type}'")

###############################################################################
# 4) Screenshot function
###############################################################################

def take_screenshot() -> bytes:
    """
    Capture a screenshot from the container (the entire X screen).
    """
    cmd = f'DISPLAY={DOCKER_DISPLAY} import -window root png:-'
    # decode=False means we get raw bytes
    screenshot_bytes = docker_exec(cmd, decode=False)
    return screenshot_bytes

###############################################################################
# 5) Main loop that sends instructions to the model and handles responses
###############################################################################

def run_cua_demo():
    """
    Demonstrates a minimal loop:
      - Send a request telling the model: "Open a terminal and type 'ls'."
      - The model returns 'computer_call' items with actions (click, etc.).
      - We run those actions with xdotool in Docker.
      - We screenshot the updated environment and feed it back.
      - We repeat until no more actions are requested.
    """

    # 5a) First request to the model
    conversation_input = [
        {
            "role": "user",
            "content": "Please open the terminal in this container, type 'ls', proceed and read the output."
        }
    ]

    response = openai.responses.create(
        model="computer-use-preview",
        tools=[
            {
                "type": "computer_use_preview",
                "display_width": 1280,
                "display_height": 800,
                "environment": "linux"  # must be one of 'windows', 'mac', 'linux', 'browser'
            }
        ],
        input=conversation_input,
        truncation="auto",
    )

    # 5b) Start the "action → screenshot → next request" loop
    while True:
        # Find 'computer_call' items from the model
        computer_calls = [item for item in response.output if item.type == "computer_call"]

        if not computer_calls:
            # No more actions requested by the model → we can show final text
            print("\nNo more actions requested. Final output from the model:")
            for item in response.output:
                if item.type == "message":
                    # Print the model's text message
                    print(item.content)
            break

        # In many workflows, you’d handle each computer call one by one.
        # We’ll loop through them, though the model often returns just one at a time.
        for call_item in computer_calls:
            action = call_item.action
            call_id = call_item.call_id
            pending_safety_checks = call_item.pending_safety_checks

            # If the model triggered any safety checks, you must confirm them before proceeding.
            # For a minimal demo, we auto-acknowledge. In production, you'd confirm with a user.
            acknowledged_safety_checks = []
            for sc in pending_safety_checks:
                print(f"[!] Safety check triggered: {sc.code} - {sc.message}")
                acknowledged_safety_checks.append(
                    {
                        "id": sc.id,
                        "code": sc.code,
                        "message": sc.message,
                    }
                )

            # 5c) Execute the action
            handle_model_action(action)

            # 5d) Wait a moment for UI to update
            time.sleep(1)

            # 5e) Take a screenshot
            screenshot_bytes = take_screenshot()
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

            # 5f) Create the next input containing that screenshot
            next_input = {
                "call_id": call_id,
                "type": "computer_call_output",
                "output": {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{screenshot_b64}"
                },
                "acknowledged_safety_checks": acknowledged_safety_checks,
                # Optionally "current_url": "...",
            }

            # Send the new screenshot back to the model, continuing the conversation
            response = openai.responses.create(
                model="computer-use-preview",
                previous_response_id=response.id,
                tools=[
                    {
                        "type": "computer_use_preview",
                        "display_width": 1280,
                        "display_height": 800,
                        "environment": "linux"
                    }
                ],
                input=[next_input],
                truncation="auto",
            )

if __name__ == "__main__":
    run_cua_demo()
