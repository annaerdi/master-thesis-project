import json
import yaml
from typing import Optional
from playbookgen.agents import RunContextWrapper, function_tool
from playbookgen.context import AppContext
from playbookgen.utils.browser_helpers import build_naive_css_selector
from playbookgen.utils.browser import do_browser_action


@function_tool
async def get_interactive_elements(ctx: RunContextWrapper[AppContext], session_id: str, output_file: str) -> str:
    sessions = ctx.context.browser_sessions
    if session_id not in sessions:
        return "No active session. Create one with 'visit' command first."

    page = sessions[session_id]
    try:
        elements = await page.query_selector_all("a, button, input, textarea, select")
        result = []

        for idx, elem in enumerate(elements, start=1):
            selector = await build_naive_css_selector(elem)
            result.append({
                "index": idx,
                "selector": f"css={selector}",
                "tag": await elem.evaluate("el => el.tagName"),
                "text": (await elem.inner_text()).strip(),
                "type": await elem.get_attribute("type"),
                "id": await elem.get_attribute("id"),
                "class": await elem.get_attribute("class")
            })

        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)

        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error collecting elements: {str(e)}"

@function_tool
async def add_playbook_step(
    ctx: RunContextWrapper[AppContext],
    step_type: str,
    seconds: Optional[int] = None,
    cmd: Optional[str] = None,
    url: Optional[str] = None,
    selector: Optional[str] = None,
    text: Optional[str] = None,
    session: Optional[str] = None,
    creates_session: Optional[str] = None,
    screenshot_path: Optional[str] = None,
) -> str:
    playbook = ctx.context.playbook
    sessions = ctx.context.browser_sessions

    if step_type == "sleep":
        if seconds is None:
            return "Missing 'seconds' for sleep step"
        step = {"type": "sleep", "seconds": seconds}
        playbook.append(step)
        return f"Added sleep step:\\n{yaml.dump(step, sort_keys=False)}"

    if cmd is None:
        return "Missing 'cmd' for browser step"

    step = {"type": step_type, "cmd": cmd}
    if url: step["url"] = url
    if selector: step["selector"] = selector
    if text: step["text"] = text
    if session: step["session"] = session
    if creates_session: step["creates_session"] = creates_session
    if screenshot_path: step["screenshot_path"] = screenshot_path

    playbook.append(step)
    await do_browser_action(step, sessions)
    return f"Added browser step:\\n{yaml.dump(step, sort_keys=False)}"
