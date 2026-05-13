"""Paginate through all DRG pages, collect full list, download relevant items."""
import asyncio
import json
from pathlib import Path
from urllib.parse import unquote
from playwright.async_api import async_playwright

OUTPUT_DIR = Path("resources/drg_samples")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Relevant to credit union / insurance intermediary firm
TARGETS = ["CQ", "CY", "RMAR", "FSA038", "FSA039", "FIN-A", "FIN-B", "REP-CRIM",
           "CCR", "RMA", "SUP", "FSA030", "FSA001", "FSA002"]


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Navigating...")
        await page.goto("https://regdata.fca.org.uk/#/layout/resources", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)

        # Set page size to 50
        await page.select_option('select.pagination-select', '50')
        await page.click('button:text("GO")')
        await page.wait_for_timeout(3000)

        all_rows = []
        page_num = 1

        while True:
            print(f"Page {page_num}...")

            # Extract table rows
            rows = await page.evaluate("""() => {
                const links = document.querySelectorAll('a[href*="/specifications/DRG/"]');
                const seen = new Set();
                const rows = [];
                for (const a of links) {
                    const tr = a.closest('tr') || a.parentElement?.parentElement;
                    if (!tr || seen.has(tr)) continue;
                    seen.add(tr);
                    const cells = tr.querySelectorAll('td');
                    if (cells.length >= 5) {
                        const fileLinks = Array.from(tr.querySelectorAll('a[href]')).map(l => ({
                            href: l.href, text: l.textContent.trim()
                        }));
                        rows.push({
                            code: cells[0]?.textContent.trim(),
                            name: cells[1]?.textContent.trim(),
                            version: cells[2]?.textContent.trim(),
                            status: cells[3]?.textContent.trim(),
                            applicableFrom: cells[4]?.textContent.trim(),
                            links: fileLinks
                        });
                    }
                }
                return rows;
            }""")

            all_rows.extend(rows)
            print(f"  Got {len(rows)} rows (total: {len(all_rows)})")

            # Try next page
            next_btn = await page.query_selector('a:text("NEXT")')
            if not next_btn:
                # Try alternative selectors
                next_btn = await page.query_selector('[aria-label="Next"]')
            if not next_btn:
                break

            is_disabled = await next_btn.evaluate("el => el.classList.contains('disabled') || el.parentElement.classList.contains('disabled')")
            if is_disabled:
                break

            await next_btn.click()
            await page.wait_for_timeout(2000)
            page_num += 1

        print(f"\nTotal DRG entries: {len(all_rows)}")
        Path(OUTPUT_DIR / "_full_drg_catalog.json").write_text(json.dumps(all_rows, indent=2))

        # Print unique data item codes
        codes = sorted(set(r['code'] for r in all_rows))
        print(f"Unique data item codes ({len(codes)}):")
        for code in codes:
            names = set(r['name'] for r in all_rows if r['code'] == code)
            print(f"  {code}: {', '.join(names)}")

        # Download relevant items (latest version, Excel + XSD)
        print(f"\n--- Downloading target items ---")
        for row in all_rows:
            code = row['code']
            if row['status'] != 'Latest':
                continue
            is_target = any(code.upper().startswith(t.upper()) for t in TARGETS)
            if not is_target:
                continue

            for link in row['links']:
                href = link['href']
                if not href.endswith(('.xlsx', '.xls', '.xsd')):
                    continue
                filename = unquote(href.split('/')[-1])
                dest = OUTPUT_DIR / filename
                if dest.exists():
                    continue
                try:
                    resp = await page.request.get(href)
                    if resp.ok:
                        dest.write_bytes(await resp.body())
                        print(f"  {code} -> {filename} ({dest.stat().st_size} bytes)")
                    else:
                        print(f"  {code} -> {filename} HTTP {resp.status}")
                except Exception as e:
                    print(f"  {code} -> {filename} FAILED: {e}")

        await browser.close()
        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
