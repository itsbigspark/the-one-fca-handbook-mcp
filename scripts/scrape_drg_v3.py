"""Scrape DRG catalog from Angular grid and download relevant files."""
import asyncio
import json
from pathlib import Path
from urllib.parse import unquote
from playwright.async_api import async_playwright

OUTPUT_DIR = Path("resources/drg_samples")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = ["CQ", "CY", "RMAR", "FSA038", "FSA039", "FIN-A", "FIN-B",
           "REP-CRIM", "CCR", "RMA", "FSA030", "FSA001", "FSA002"]


async def extract_rows(page):
    """Extract rows from the Angular grid."""
    return await page.evaluate("""() => {
        const bodyRows = document.querySelectorAll('.body-row');
        const results = [];
        for (const row of bodyRows) {
            const cols = row.querySelectorAll('.content-col, .col');
            const texts = Array.from(cols).map(c => c.textContent.trim());
            const links = Array.from(row.querySelectorAll('a[href]')).map(a => ({
                href: a.href, text: a.textContent.trim()
            }));
            if (texts.length >= 3) {
                results.push({texts, links});
            }
        }
        return results;
    }""")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Navigating...")
        await page.goto("https://regdata.fca.org.uk/#/layout/resources", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)

        # Set page size to 50
        await page.select_option('select.pagination-select', '50')
        await page.click('button.pagination-go-button')
        await page.wait_for_timeout(3000)

        all_rows = []
        page_num = 1

        while True:
            print(f"Page {page_num}...")
            rows = await extract_rows(page)
            print(f"  Got {len(rows)} rows")

            for row in rows:
                texts = row['texts']
                # Parse: code, name, version, status, applicable_from, then link columns
                entry = {
                    'code': texts[0] if len(texts) > 0 else '',
                    'name': texts[1] if len(texts) > 1 else '',
                    'version': texts[2] if len(texts) > 2 else '',
                    'status': texts[3] if len(texts) > 3 else '',
                    'applicable_from': texts[4] if len(texts) > 4 else '',
                    'links': row['links']
                }
                all_rows.append(entry)

            # Next page
            next_link = await page.query_selector('.page-item:last-child:not(.disabled) a, a:text("NEXT")')
            if not next_link:
                break
            # Check if we're on the last page
            active_page = await page.evaluate("""() => {
                const active = document.querySelector('.page-item.active a');
                return active ? active.textContent.trim() : '';
            }""")
            last_page = await page.evaluate("""() => {
                const items = document.querySelectorAll('.page-item a');
                const nums = Array.from(items).map(a => parseInt(a.textContent)).filter(n => !isNaN(n));
                return Math.max(...nums);
            }""")
            print(f"  Active page: {active_page}, Last: {last_page}")

            if int(active_page or 0) >= last_page:
                break

            await next_link.click()
            await page.wait_for_timeout(2000)
            page_num += 1

        print(f"\nTotal entries: {len(all_rows)}")

        # Save full catalog
        Path(OUTPUT_DIR / "_full_drg_catalog.json").write_text(json.dumps(all_rows, indent=2))

        # Print unique codes
        codes = sorted(set(r['code'] for r in all_rows if r['code']))
        print(f"Unique data item codes ({len(codes)}):")
        for code in codes:
            latest = [r for r in all_rows if r['code'] == code and r['status'] == 'Latest']
            name = latest[0]['name'] if latest else ''
            print(f"  {code}: {name}")

        # Download targets
        print(f"\n--- Downloading targets ---")
        for row in all_rows:
            code = row['code']
            if row['status'] != 'Latest':
                continue
            is_target = any(code.upper().startswith(t.upper()) for t in TARGETS)
            if not is_target:
                continue

            for link in row['links']:
                href = link['href']
                if not any(href.endswith(ext) for ext in ('.xlsx', '.xls', '.xsd')):
                    continue
                filename = unquote(href.split('/')[-1])
                dest = OUTPUT_DIR / filename
                if dest.exists():
                    continue
                try:
                    resp = await page.request.get(href)
                    if resp.ok:
                        body = await resp.body()
                        dest.write_bytes(body)
                        print(f"  {code} -> {filename} ({len(body)} bytes)")
                except Exception as e:
                    print(f"  {code} -> {filename} FAILED: {e}")

        await browser.close()
        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
