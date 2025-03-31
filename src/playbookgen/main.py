import asyncio
from dotenv import load_dotenv
from agents import Runner
from playbookgen.agent import create_browser_agent
from playbookgen.context import AppContext
from playbookgen.utils.browser import shutdown_playwright


async def main():
    load_dotenv()
    ctx = AppContext(browser_sessions={}, playbook=[])
    agent = create_browser_agent()

    while True:
        try:
            user_input = input("User: ")
            if not user_input.strip():
                print("Exiting...")
                break

            result = await Runner.run(
                starting_agent=agent,
                input=user_input,
                context=ctx,
                max_turns=50,
            )
            print("Assistant:", result.final_output)

        except KeyboardInterrupt:
            print("\\nExiting...")
            break

        finally:
            # Gracefully close all browser pages
            for session in ctx.browser_sessions.values():
                try:
                    await session.context.close()
                except Exception:
                    pass
            await shutdown_playwright()

if __name__ == "__main__":
    asyncio.run(main())
