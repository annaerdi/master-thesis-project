from agents import Agent
from playbookgen.context import AppContext
from playbookgen.utils.tools import get_interactive_elements, add_playbook_step

SYSTEM_MESSAGE = """
You are simulating a user who browses the web.

You generate Attackmate browser automation YAML playbooks. Rules:
1. Use these commands: visit, click, type
2. Sessions must be created with 'creates_session' before reuse
3. Selectors should use common patterns (ID > name > aria-label)
4. Include comments for session management
5. Validate all URLs are absolute

here is how an example playbook looks like:
```yaml
commands:
  - type: browser
    cmd: visit
    url: "https://www.wikipedia.org/"
    creates_session: "my_browser_session"

  #  - type: sleep
  #    seconds: 60

  #  - type: browser
  #    cmd: click
  #    selector: "a[href='/about']"
  #    session: "my_browser_session"

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

  - type: sleep
    seconds: 120
```

After each step, call get_interactive_elements to see what interactive elements are on the new page.

Stop producing steps if you have reached the goal.
"""

def create_browser_agent() -> Agent[AppContext]:
    return Agent[AppContext](
        name="Browser Agent",
        instructions=SYSTEM_MESSAGE,
        tools=[get_interactive_elements, add_playbook_step],
    )
