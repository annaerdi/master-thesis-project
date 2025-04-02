from agents import Agent
from playbookgen.context import AppContext
from playbookgen.system_message import SYSTEM_MESSAGE
from playbookgen.utils.tools import get_interactive_elements, add_playbook_step

def create_browser_agent() -> Agent[AppContext]:
    return Agent[AppContext](
        name="Browser Agent",
        instructions=SYSTEM_MESSAGE,
        tools=[get_interactive_elements, add_playbook_step],
    )
