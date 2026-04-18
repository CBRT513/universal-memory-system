# MCP Chrome Bridge Integration
from playwright.async_api import async_playwright

async def connect_to_chrome():
    async with async_playwright() as p:
        # Connect to existing Chrome instance
        browser = await p.chromium.connect_over_cdp('http://localhost:9222')
        page = await browser.new_page()
        await page.goto('https://example.com')
        # Agent can now control the browser
        return page
