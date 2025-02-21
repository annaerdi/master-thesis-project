"""
source: https://cookbook.openai.com/examples/orchestrating_agents

sample result of the execution:
-------------------------------
$ python example.py
User: hi
Assistant: Hello! How can I assist you today?
User: i want a refund on my hairdryer
Assistant: Could you please tell me why you're requesting a refund for your hairdryer?
User: it doesnt work. i tried to plug it in the outlet
Assistant: Have you tried using a different outlet or checking if the power source is functioning properly?
User: yes
Assistant: I apologize for the inconvenience. I can initiate the refund process for you. Please hold on for a moment while I look up the item ID for your hairdryer.
Assistant: look_up_item({'search_query': 'hairdryer'})
Assistant: execute_refund({'item_id': 'item_132612938', 'reason': "Doesn't work despite trying different outlets."})
Summary: item_132612938 Doesn't work despite trying different outlets.
Assistant: Your refund has been successfully processed for the hairdryer. If you need further assistance, feel free to ask!
"""
from openai import OpenAI
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from helper import function_to_schema
import json


load_dotenv()
client = OpenAI()

# Customer Service Routine

system_message = (
    "You are a customer support agent for ACME Inc."
    "Always answer in a sentence or less."
    "Follow the following routine with the user:"
    "1. First, ask probing questions and understand the user's problem deeper.\n"
    " - unless the user has already provided a reason.\n"
    "2. Propose a fix (make one up).\n"
    "3. ONLY if not satesfied, offer a refund.\n"
    "4. If accepted, search for the ID and then execute refund."
    ""
)

def look_up_item(search_query):
    """Use to find item ID.
    Search query can be a description or keywords."""

    # return hard-coded item ID - in reality would be a lookup
    return "item_132612938"


def execute_refund(item_id, reason="not provided"):

    print("Summary:", item_id, reason) # lazy summary
    return "success"

tools = [execute_refund, look_up_item]


def run_full_turn(system_message, tools, messages):

    num_init_messages = len(messages)
    messages = messages.copy()

    while True:

        # turn python functions into tools and save a reverse map
        tool_schemas = [function_to_schema(tool) for tool in tools]
        tools_map = {tool.__name__: tool for tool in tools}

        # === 1. get openai completion ===
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_message}] + messages,
            tools=tool_schemas or None,
        )
        message = response.choices[0].message
        messages.append(message)

        if message.content:  # print assistant response
            print("Assistant:", message.content)

        if not message.tool_calls:  # if finished handling tool calls, break
            break

        # === 2. handle tool calls ===

        for tool_call in message.tool_calls:
            result = execute_tool_call(tool_call, tools_map)

            result_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            }
            messages.append(result_message)

    # ==== 3. return new messages =====
    return messages[num_init_messages:]


def execute_tool_call(tool_call, tools_map):
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)

    print(f"Assistant: {name}({args})")

    # call corresponding function with provided arguments
    return tools_map[name](**args)


messages = []
while True:
    user = input("User: ")
    messages.append({"role": "user", "content": user})

    new_messages = run_full_turn(system_message, tools, messages)
    messages.extend(new_messages)
