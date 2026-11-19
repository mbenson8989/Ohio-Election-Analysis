"""Download files by clicking links (matched by visible text) on a public SOS page, in the CDP Chrome."""
import sys, asyncio
from playwright.async_api import async_playwright
async def main(page_url, outdir, names):
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://127.0.0.1:9333')
        ctx = b.contexts[0]; pg = ctx.pages[0]
        cdp = await b.new_browser_cdp_session()
        await cdp.send('Browser.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': outdir, 'eventsEnabled': True})
        await pg.goto(page_url, wait_until='domcontentloaded', timeout=90000); await pg.wait_for_timeout(3000)
        for n in names:
            loc = pg.locator('a', has_text=n).first
            async with pg.expect_download(timeout=1800000) as di:
                await loc.click()
            d = await di.value
            print('started', n, d.suggested_filename, flush=True)
            import os
            f = outdir + '/' + d.suggested_filename
            for _ in range(3600):
                await pg.wait_for_timeout(1000)
                if os.path.exists(f) and not any(x.endswith('.crdownload') for x in os.listdir(outdir)): break
            print('saved', n, d.suggested_filename, flush=True)
asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3:]))
