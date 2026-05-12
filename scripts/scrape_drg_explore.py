"""Scroll and expand all sections on RegData resources to get complete DRG list."""
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

        print("Navigating...")
        await page.goto("https://regdata.fca.org.uk/#/layout/resources", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(5000)

        # Try to expand all / show all / paginate
        # First let's see what interactive elements exist
        buttons = await page.evaluate("""() => {
            const btns = document.querySelectorAll('button, [role=button], .btn, input[type=button], select');
            return Array.from(btns).map(b => ({
                tag: b.tagName,
                text: b.textContent.trim().substring(0, 80),
                type: b.type || '',
                className: b.className.substring(0, 80),
                id: b.id
            }));
        }""")
        print(f"Found {len(buttons)} interactive elements:")
        for b in buttons:
            print(f"  [{b['tag']}] {b['text'][:50]} (class={b['className'][:30]})")

        # Check for pagination or "show more" or select/dropdown for page size
        selects = await page.query_selector_all('select')
        print(f"\nFound {len(selects)} select elements")
        for i, sel in enumerate(selects):
            options = await sel.evaluate("""el => {
                return Array.from(el.options).map(o => ({value: o.value, text: o.text}));
            }""")
            print(f"  Select {i}: {options}")

        # Try scrolling to bottom repeatedly to trigger lazy load
        prev_count = 0
        for i in range(10):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            count = await page.evaluate("""() => document.querySelectorAll('a[href*="/specifications/DRG/"]').length""")
            print(f"  Scroll {i+1}: {count} DRG links")
            if count == prev_count:
                break
            prev_count = count

        # Click any "next page" or expand buttons
        next_btns = await page.query_selector_all('[aria-label*="next"], [aria-label*="Next"], .next, .pagination-next')
        print(f"\nPagination buttons: {len(next_btns)}")

        # Get all visible text to understand page structure
        page_text = await page.evaluate("""() => {
            const main = document.querySelector('main') || document.querySelector('[role=main]') || document.body;
            return main.innerText.substring(0, 5000);
        }""")
        print(f"\nPage text (first 3000 chars):\n{page_text[:3000]}")

        # Get all links with DRG in path
        all_links = await page.evaluate("""() => {
            const anchors = document.querySelectorAll('a[href*="specifications"]');
            return Array.from(anchors).map(a => ({
                href: a.href,
                text: a.textContent.trim(),
                parent: a.parentElement?.parentElement?.textContent?.trim().substring(0, 150) || ''
            }));
        }""")
        print(f"\nAll specification links: {len(all_links)}")
        Path(OUTPUT_DIR / "_all_spec_links.json").write_text(json.dumps(all_links, indent=2))

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
