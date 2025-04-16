import asyncio
from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServerSse
from agents.model_settings import ModelSettings

async def run(agent: Agent):
    user_message = (
        "You are an LLM simulating a CAS (Central Alarm System) operator using ZoneMinder by accessing http://40.118.57.244/zm/ "
        "with username admin and password thIs_i5_A_tESt_PasSw0Rd, where your task is to log in. "
        "Check system logs and alerts, behave like a real operator (focused, attentive, thorough), and create a new user "
        "(testuser / anoTH3er_tESt_PasSw0Rd) without switching accounts. Once you created the user, you get back to your "
        "regular CAS operator tasks, acting naturally and exploring the interface unscripted within a 5-minute session. "
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
