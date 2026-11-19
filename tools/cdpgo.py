import sys, asyncio, json, re
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://127.0.0.1:9333')
        pg = b.contexts[0].pages[0]
        for u in sys.argv[1:]:
            try: await pg.goto(u, wait_until='domcontentloaded', timeout=60000)
            except Exception as e: print('ERR', e)
            await pg.wait_for_timeout(3000)
            print('##', u, '->', pg.url, '|', await pg.title())
            links = await pg.eval_on_selector_all('a', 'els=>els.map(e=>[e.innerText.trim().slice(0,90), e.href])')
            for t,h in links:
                if re.search(r'xlsx|xls|csv|pdf|txt|gz|zip|result|turnout|voter|regist|affil|data|2022|2026|primary', (t+h), re.I):
                    print('  ', t.replace('\n',' '), '|', h)
asyncio.run(main())
