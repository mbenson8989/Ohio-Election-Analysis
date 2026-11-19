"""DATA Act daily snapshot search on data.ohiosos.gov/voter, using the page's own search (OnSearch)."""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main(start, end, counties):
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://127.0.0.1:9333')
        pg = b.contexts[0].pages[0]
        if 'data.ohiosos.gov/voter' not in pg.url:
            await pg.goto('https://data.ohiosos.gov/voter', wait_until='networkidle', timeout=90000)
        r = await pg.evaluate("""async ([s,e,c])=>{
            const fd = new URLSearchParams();
            fd.append('__RequestVerificationToken', document.querySelector('input[name="__RequestVerificationToken"]').value);
            fd.append('STARTDT', s); fd.append('ENDDT', e); fd.append('ELECTIONDT','');
            for (const x of c) fd.append('COUNTYLIST[]', x);
            const r = await fetch('/voter/Home/OnSearch', {method:'POST', body: fd, headers:{'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8','X-Requested-With':'XMLHttpRequest'}});
            return await r.text(); }""", [start, end, counties])
        print(r)
asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3].split(',')))
