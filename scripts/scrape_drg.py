"""Scrape FCA RegData resources page for DRG download links and grab sample files."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_DIR = Path("resources/drg_samples")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Navigating to RegData resources page...")
        await page.goto("https://regdata.fca.org.uk/#/layout/resources", wait_until="networkidle", timeout=60000)

        # Wait for content to render
        await page.wait_for_timeout(5000)

        # Get page content to understand structure
        content = await page.content()
        Path(OUTPUT_DIR / "_page_source.html").write_text(content)
        print(f"Saved page source ({len(content)} chars)")

        # Look for links to downloadable files (xsd, xlsx, xls, pdf)
        links = await page.evaluate("""() => {
            const anchors = document.querySelectorAll('a[href]');
            const results = [];
            for (const a of anchors) {
                const href = a.href || '';
                const text = a.textContent.trim();
                if (href.match(/\\.(xsd|xlsx?|pdf|zip|csv)$/i) || 
                    text.match(/data reference guide|drg|template|schema/i) ||
                    href.match(/download|resource|guide/i)) {
                    results.push({href, text: text.substring(0, 100)});
                }
            }
            return results;
        }""")

        print(f"\nFound {len(links)} potential resource links:")
        for link in links[:50]:
            print(f"  {link['text'][:60]} -> {link['href'][:100]}")

        # Save all links
        Path(OUTPUT_DIR / "_resource_links.json").write_text(json.dumps(links, indent=2))

        # Also look for any tables or lists of resources
        tables = await page.evaluate("""() => {
            const tables = document.querySelectorAll('table');
            const results = [];
            for (const t of tables) {
                const rows = t.querySelectorAll('tr');
                const tableData = [];
                for (const row of rows) {
                    const cells = row.querySelectorAll('td, th');
                    tableData.push(Array.from(cells).map(c => c.textContent.trim().substring(0, 80)));
                }
                if (tableData.length > 0) results.push(tableData);
            }
            return results;
        }""")

        if tables:
            print(f"\nFound {len(tables)} tables on page")
            Path(OUTPUT_DIR / "_tables.json").write_text(json.dumps(tables, indent=2))

        # Look for any expandable sections or tabs
        sections = await page.evaluate("""() => {
            const headings = document.querySelectorAll('h1, h2, h3, h4, .panel-title, .accordion-header, [role=tab]');
            return Array.from(headings).map(h => h.textContent.trim().substring(0, 100));
        }""")

        if sections:
            print(f"\nPage sections/headings:")
            for s in sections[:30]:
                print(f"  {s}")

        # Try clicking on any "Data Reference Guides" section if it exists
        drg_elements = await page.query_selector_all('text=Data Reference Guide')
        if drg_elements:
            print(f"\nFound {len(drg_elements)} DRG elements, clicking first...")
            await drg_elements[0].click()
            await page.wait_for_timeout(3000)

            # Re-check for download links after click
            links_after = await page.evaluate("""() => {
                const anchors = document.querySelectorAll('a[href]');
                const results = [];
                for (const a of anchors) {
                    const href = a.href || '';
                    const text = a.textContent.trim();
                    if (href.match(/\\.(xsd|xlsx?|pdf|zip|csv)$/i)) {
                        results.push({href, text: text.substring(0, 100)});
                    }
                }
                return results;
            }""")
            if links_after:
                print(f"After click, found {len(links_after)} file links")
                Path(OUTPUT_DIR / "_resource_links_after_click.json").write_text(json.dumps(links_after, indent=2))

        # Download first few Excel/XSD files if found
        all_file_links = [l for l in links if any(l['href'].endswith(ext) for ext in ['.xsd', '.xlsx', '.xls', '.zip'])]
        for link in all_file_links[:5]:
            try:
                print(f"\nDownloading: {link['text'][:40]}...")
                async with page.expect_download(timeout=30000) as download_info:
                    await page.evaluate(f"window.location.href = '{link['href']}'")
                download = await download_info.value
                dest = OUTPUT_DIR / download.suggested_filename
                await download.save_as(str(dest))
                print(f"  Saved: {dest}")
            except Exception as e:
                print(f"  Failed: {e}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
