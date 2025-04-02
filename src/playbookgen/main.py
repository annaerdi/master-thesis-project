import asyncio
import json
import uuid
from dotenv import load_dotenv
from pydantic import BaseModel

from agents import (
    Agent,
    Runner,
    MessageOutputItem,
    ToolCallOutputItem,
    ToolCallItem,
    HandoffOutputItem,
    ItemHelpers,
    TResponseInputItem,
    trace
)
from playbookgen.browser_agent import create_browser_agent
from playbookgen.user_simulation_agent import create_user_simulation_agent
from playbookgen.utils.browser import shutdown_playwright

class AppContext(BaseModel):
    browser_sessions: dict = {}
    playbook: list = []
    current_page_summary: str = ""
    last_interactive_elements: list = []
    user_goal: str = ""


async def main():
    load_dotenv()

    # Initialize agents
    browser_agent = create_browser_agent()
    user_sim_agent = create_user_simulation_agent()

    # Setup shared context
    ctx = AppContext()
    ctx.user_goal = input("What's the user's goal? ")

    current_agent: Agent[AppContext] = user_sim_agent
    input_items: list[TResponseInputItem] = []
    conversation_id = uuid.uuid4().hex[:16]

    while True:
        user_input_text = f"Goal: {ctx.user_goal}\n\nPage Summary: {ctx.current_page_summary}\n\nInteractive Elements: {ctx.last_interactive_elements}"

        with trace("Browser Sim", group_id=conversation_id):
            input_items.append({"content": user_input_text, "role": "user"})
            result = await Runner.run(current_agent, input_items, context=ctx)

            for new_item in result.new_items:
                agent_name = new_item.agent.name

                if isinstance(new_item, MessageOutputItem):
                    content = ItemHelpers.text_message_output(new_item)
                    print(f"{agent_name}: {content}")

                    if content.strip().upper() == "DONE":
                        print("\n🎉 Task complete! Exiting.")
                        return

                    try:
                        step = json.loads(content)
                        step_text = json.dumps(step)

                        # 🧠 Handoff to Browser Agent
                        result = await Runner.run(
                            browser_agent,
                            [{"content": step_text, "role": "user"}],
                            context=ctx
                        )

                        for b_item in result.new_items:
                            if isinstance(b_item, ToolCallOutputItem):
                                print(f"{b_item.agent.name}: Tool call output: {b_item.output}")
                            elif isinstance(b_item, MessageOutputItem):
                                print(f"{b_item.agent.name}: {ItemHelpers.text_message_output(b_item)}")

                        current_agent = user_sim_agent

                    except json.JSONDecodeError:
                        print("⚠️ Invalid JSON format from UserSimAgent, skipping this step.")
                        continue

                elif isinstance(new_item, ToolCallItem):
                    print(f"{agent_name}: Calling a tool...")

                elif isinstance(new_item, ToolCallOutputItem):
                    print(f"{agent_name}: Tool call output: {new_item.output}")

                elif isinstance(new_item, HandoffOutputItem):
                    print(f"Handed off from {new_item.source_agent.name} to {new_item.target_agent.name}")

            input_items = result.to_input_list()

    # Cleanup
    for session in ctx.browser_sessions.values():
        try:
            await session.context.close()
        except Exception:
            pass
    await shutdown_playwright()


if __name__ == "__main__":
    asyncio.run(main())