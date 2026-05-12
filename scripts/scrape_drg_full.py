"""Scrape full DRG list and download relevant samples for credit union demo."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_DIR = Path("resources/drg_samples")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Data items likely relevant to our credit union firm
TARGETS = ["CQ", "CY", "RMAR", "FSA038", "FSA039", "FIN", "REP-CRIM", "CCR"]


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Navigating to RegData resources page...")
        await page.goto("https://regdata.fca.org.uk/#/layout/resources", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(5000)

        # Scroll to load all content and find all DRG links
        all_links = await page.evaluate("""() => {
            const anchors = document.querySelectorAll('a[href]');
            const results = [];
            for (const a of anchors) {
                const href = a.href || '';
                if (href.includes('/specifications/DRG/')) {
                    const text = a.textContent.trim();
                    const row = a.closest('tr');
                    let rowText = '';
                    if (row) rowText = row.textContent.replace(/\\s+/g, ' ').trim().substring(0, 200);
                    results.push({href, text, rowText});
                }
            }
            return results;
        }""")

        print(f"Found {len(all_links)} total DRG links")
        Path(OUTPUT_DIR / "_all_drg_links.json").write_text(json.dumps(all_links, indent=2))

        # Get the full table data
        table_data = await page.evaluate("""() => {
            const table = document.querySelector('table');
            if (!table) return [];
            const rows = table.querySelectorAll('tr');
            const data = [];
            for (const row of rows) {
                const cells = row.querySelectorAll('td, th');
                const rowData = Array.from(cells).map(c => ({
                    text: c.textContent.trim().substring(0, 100),
                    links: Array.from(c.querySelectorAll('a')).map(a => ({
                        href: a.href,
                        text: a.textContent.trim()
                    }))
                }));
                if (rowData.length > 0) data.push(rowData);
            }
            return data;
        }""")

        print(f"Table has {len(table_data)} rows")
        Path(OUTPUT_DIR / "_full_table.json").write_text(json.dumps(table_data, indent=2))

        # Find and download target data items
        target_links = []
        for link in all_links:
            href = link['href']
            for target in TARGETS:
                if f"/DRG/{target}" in href or f"/DRG/{target.lower()}" in href:
                    target_links.append(link)
                    break

        # Also grab xlsx/xls files preferentially
        xlsx_links = [l for l in target_links if l['href'].endswith(('.xlsx', '.xls'))]
        xsd_links = [l for l in target_links if l['href'].endswith('.xsd')]

        print(f"\nTarget data item links: {len(target_links)} ({len(xlsx_links)} Excel, {len(xsd_links)} XSD)")

        # Download Excel files for targets
        to_download = xlsx_links[:8] + xsd_links[:4]
        for link in to_download:
            url = link['href']
            filename = url.split('/')[-1]
            dest = OUTPUT_DIR / filename
            if dest.exists():
                print(f"  Already have: {filename}")
                continue
            try:
                print(f"  Downloading: {filename}...")
                resp = await page.request.get(url)
                if resp.ok:
                    content = await resp.body()
                    dest.write_bytes(content)
                    print(f"    Saved ({len(content)} bytes)")
                else:
                    print(f"    HTTP {resp.status}")
            except Exception as e:
                print(f"    Failed: {e}")

        # Also grab the common change log XSD if available
        common_links = [l for l in all_links if 'Common' in l['href']]
        for link in common_links[:2]:
            url = link['href']
            filename = url.split('/')[-1]
            dest = OUTPUT_DIR / filename
            if dest.exists():
                continue
            try:
                resp = await page.request.get(url)
                if resp.ok:
                    dest.write_bytes(await resp.body())
                    print(f"  Common: {filename} ({len(await resp.body())} bytes)")
            except Exception:
                pass

        await browser.close()
        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
