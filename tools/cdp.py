import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://127.0.0.1:9333')
        ctx = b.contexts[0]
        for pg in ctx.pages:
            print(pg.url, await pg.title())
        pg = ctx.pages[0]
        await pg.screenshot(path='/tmp/sos/shot.png')
asyncio.run(main())
