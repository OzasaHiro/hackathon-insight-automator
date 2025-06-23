#!/usr/bin/env python3
"""
Debug script to test Playwright browser functionality.
"""
import asyncio
import sys
from playwright.async_api import async_playwright

async def test_browsers():
    """Test different browsers to see which one works."""
    async with async_playwright() as p:
        browsers = [
            ("Chromium", p.chromium),
            ("Firefox", p.firefox),
            ("WebKit", p.webkit)
        ]
        
        for name, browser_type in browsers:
            print(f"\n=== Testing {name} ===")
            try:
                # Test headless mode
                print("Testing headless mode...")
                browser = await browser_type.launch(headless=True, timeout=30000)
                page = await browser.new_page()
                await page.goto("https://www.google.com", timeout=30000)
                title = await page.title()
                print(f"✅ {name} headless: {title}")
                await browser.close()
                
                # Test non-headless mode
                print("Testing non-headless mode...")
                browser = await browser_type.launch(headless=False, timeout=30000)
                page = await browser.new_page()
                await page.goto("https://www.google.com", timeout=30000)
                title = await page.title()
                print(f"✅ {name} non-headless: {title}")
                await browser.close()
                
            except Exception as e:
                print(f"❌ {name} failed: {e}")

if __name__ == "__main__":
    print("Testing Playwright browsers...")
    asyncio.run(test_browsers())