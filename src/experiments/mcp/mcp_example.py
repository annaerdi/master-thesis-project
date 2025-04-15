import asyncio
from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServerSse
from agents.model_settings import ModelSettings

async def run(agent: Agent):
    print("Asking the agent to open Google and search for 'OpenAI'...")
    user_message = (
        "Please open google.com, search for 'OpenAI', and give me a snapshot of the results."
    )
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
                ),
                mcp_servers=[playwright_server],
                # Force the model to use a tool if needed
                model_settings=ModelSettings(tool_choice="required"),
            )

            await run(agent)

if __name__ == "__main__":
    asyncio.run(main())
