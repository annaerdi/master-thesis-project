import asyncio
from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServerSse
from agents.model_settings import ModelSettings

async def run(agent: Agent):
    user_message = (
        "You are simulating the behavior of a Central Alarm System (CAS) operator using ZoneMinder. "
        "Log in to http://40.118.57.244/zm/ with username `admin` and password `thIs_i5_A_tESt_PasSw0Rd`. "
        "Once logged in, behave like a real operator: focus on monitoring camera feeds, checking system alerts and logs, "
        "and exploring the interface naturally and attentively. You should act as if you are responsible for system awareness and safety. "
        "In addition to your monitoring duties, you have been instructed to create a new user in the system. "
        "Use the credentials: username `testuser6`, password `Test1234`. If `testuser6` already exists, increment the number. "
        "Do not switch accounts — stay logged in as admin after creating the user. "
        "Treat this like a real work session: move between sections like Console, Logs, or Montage, investigate timestamps, and behave realistically. "
        "Act without needing step-by-step instructions, and approach the task with a cautious and observant personality. "
        "After completing your duties, log out. The session should last no more than 5 minutes."
    )
    print("User prompt:", user_message)
    result = await Runner.run(starting_agent=agent, input=user_message, max_turns=50)
    print("\nFinal output from the agent:")
    print(result.final_output)

async def main():
    # Connect to the Playwright MCP SSE endpoint
    async with MCPServerSse(
        name="Playwright MCP",
        params={
            "url": "http://localhost:8001/sse",  # Matches the `--port=8001` from above
        },
    ) as playwright_server:
        # Generate a trace ID so you can view logs in OpenAI's trace viewer (optional)
        trace_id = gen_trace_id()

        # "trace()" is optional, but if you have the OpenAI trace viewer set up, it helps debugging
        with trace(workflow_name="Playwright Example", trace_id=trace_id):
            print(f"View trace (if using the OpenAI trace viewer): "
                  f"https://platform.openai.com/traces/trace?trace_id={trace_id}\n")

            # Create the agent that has access to the Playwright MCP server
            agent = Agent(
                name="Assistant",
                # Provide instructions so the agent knows it should use the browser tools:
                instructions=(
                    "You are a helpful assistant with access to Playwright browser tools. "
                    "When the user requests something involving the web, you must call the appropriate browser tool."
                    "Also, at the end of your task you must generate a yaml playbook for the actions you took."
                    """
                    Here is how an example playbook looks like:
                    ```yaml
                    commands:
                      - type: browser
                        cmd: visit
                        url: "https://www.wikipedia.org/"
                        creates_session: "my_browser_session"

                      - type: browser
                        cmd: click
                        selector: "a[href='/about']"
                        session: "my_browser_session"
                    
                      - type: browser
                        cmd: type
                        selector: "input[id='searchInput']"
                        text: "Testing"
                        session: "my_browser_session"
                    
                      - type: browser
                        cmd: click
                        selector: "button[type='submit']"
                        session: "my_browser_session"
                    
                      - type: browser
                        cmd: click
                        selector: "input[name='btnK']"
                        session: "my_browser_session"
                    ```
                    Make sure you use CSS selectors and not aria labels for the final playbook!
                    """
                ),
                mcp_servers=[playwright_server],
                # Force the model to use a tool if needed
                model_settings=ModelSettings(tool_choice="required"),
            )

            await run(agent)

if __name__ == "__main__":
    asyncio.run(main())
