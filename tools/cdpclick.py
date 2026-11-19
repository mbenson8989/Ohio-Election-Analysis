import sys, asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://127.0.0.1:9333')
        pg = b.contexts[0].pages[0]
        await pg.mouse.move(300, 700); await pg.wait_for_timeout(400)
        await pg.mouse.click(int(sys.argv[1]), int(sys.argv[2]))
        await pg.wait_for_timeout(12000)
        print(pg.url, await pg.title())
        await pg.screenshot(path='/tmp/sos/shot2.png')
asyncio.run(main())
