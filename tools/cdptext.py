import sys, asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://127.0.0.1:9333')
        pg = b.contexts[0].pages[0]
        if sys.argv[1] != '-': 
            await pg.goto(sys.argv[1], wait_until='networkidle', timeout=90000)
        await pg.wait_for_timeout(int(sys.argv[2]) if len(sys.argv)>2 else 2000)
        print(pg.url); print(await pg.evaluate('document.body.innerText'))
        await pg.screenshot(path='/tmp/sos/shot.png', full_page=True)
        open('/tmp/sos/cur.html','w').write(await pg.content())
asyncio.run(main())
