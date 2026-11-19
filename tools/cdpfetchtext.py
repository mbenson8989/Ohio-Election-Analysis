import sys, asyncio
from playwright.async_api import async_playwright
async def main(u):
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://127.0.0.1:9333')
        pg = b.contexts[0].pages[0]
        t = await pg.evaluate("async (u)=>{const r=await fetch(u); return await r.text()}", u)
        print(t)
asyncio.run(main(sys.argv[1]))
