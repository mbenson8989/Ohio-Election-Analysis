"""Open public ohiosos.gov pages in a real (headed) Chrome so the Cloudflare
browser check can run, then save page HTML / download files."""
import sys, asyncio, os, json
from playwright.async_api import async_playwright
PROFILE = '/workspace/Ohio/.chrome-profile'
async def main(urls, outdir):
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(PROFILE, executable_path='/usr/bin/google-chrome',
              headless=False, accept_downloads=True, args=['--no-first-run'])
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        for u in urls:
            try:
                await page.goto(u, wait_until='domcontentloaded', timeout=60000)
            except Exception as e:
                print('goto err', u, e)
            for _ in range(30):
                t = await page.title()
                if 'Maintenance' not in t and 'moment' not in t.lower(): break
                await page.wait_for_timeout(1000)
            t = await page.title(); html = await page.content()
            fn = os.path.join(outdir, 'page_' + str(abs(hash(u)))[:10] + '.html')
            open(fn, 'w').write(html)
            print(json.dumps(dict(url=u, title=t, file=fn, len=len(html))))
        await ctx.close()
asyncio.run(main(sys.argv[2:], sys.argv[1]))
