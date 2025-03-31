from playwright.async_api import async_playwright, Page

playwright_instance = None  # global handle

async def launch_browser() -> Page:
    global playwright_instance
    if playwright_instance is None:
        playwright_instance = await async_playwright().start()

    browser = await playwright_instance.chromium.launch(headless=True)
    page = await browser.new_page()
    return page

async def do_browser_action(step: dict, sessions: dict):
    if step.get("type") != "browser":
        return

    cmd = step["cmd"]
    session = step.get("session")
    creates_session = step.get("creates_session")

    if creates_session:
        page = await launch_browser()
        sessions[creates_session] = page
        session = creates_session

    page = sessions.get(session)
    if not page:
        return

    if cmd == "visit":
        await page.goto(step["url"])
    elif cmd == "click" and "selector" in step:
        await page.click(step["selector"])
    elif cmd == "type" and "selector" in step:
        await page.fill(step["selector"], step.get("text", ""))
    elif cmd == "screenshot":
        await page.screenshot(path=step.get("screenshot_path", "screenshot.png"))

async def shutdown_playwright():
    global playwright_instance
    if playwright_instance is not None:
        await playwright_instance.stop()
        playwright_instance = None
