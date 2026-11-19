"""Download single DATA Act snapshot files via the page's single-file link (/voter/Home/RetreiveFile?fileNumber=...)."""
import sys, asyncio, os
from playwright.async_api import async_playwright
async def main(outdir, names):
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://127.0.0.1:9333')
        pg = b.contexts[0].pages[0]
        cdp = await b.new_browser_cdp_session()
        await cdp.send('Browser.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': outdir, 'eventsEnabled': True})
        for n in names:
            f = os.path.join(outdir, n)
            if os.path.exists(f): print('have', n); continue
            async with pg.expect_download(timeout=600000) as di:
                await pg.evaluate("(n)=>{const a=document.createElement('a'); a.href='/voter/Home/RetreiveFile?fileNumber='+n; document.body.appendChild(a); a.click(); a.remove();}", n)
            d = await di.value
            for _ in range(3600):
                await pg.wait_for_timeout(500)
                if os.path.exists(os.path.join(outdir, d.suggested_filename)) and not any(x.endswith('.crdownload') for x in os.listdir(outdir)): break
            print('saved', n, d.suggested_filename, os.path.getsize(os.path.join(outdir, d.suggested_filename)), flush=True)
asyncio.run(main(sys.argv[1], sys.argv[2:]))
