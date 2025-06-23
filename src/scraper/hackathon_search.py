"""
Hackathon search functionality for finding recent AI-related hackathons.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin
from dataclasses import dataclass

from playwright.async_api import Page, Browser
from pydantic import BaseModel, HttpUrl

logger = logging.getLogger(__name__)


@dataclass
class HackathonSearchResult:
    """Represents a hackathon found in search results."""
    name: str
    url: str
    deadline: Optional[datetime] = None
    participants: Optional[int] = None
    prizes: Optional[str] = None
    status: str = "ended"
    description: Optional[str] = None


class HackathonSearcher:
    """Searches for hackathons on Devpost based on criteria."""
    
    DEFAULT_SEARCH_URL = (
        "https://devpost.com/hackathons"
        "?length[]=days"
        "&order_by=deadline"
        "&status[]=ended"
        "&themes[]=Machine%20Learning%2FAI"
    )
    
    def __init__(self, browser: Browser):
        """
        Initialize the hackathon searcher.
        
        Args:
            browser: Playwright browser instance
        """
        self.browser = browser
        
    async def _get_page(self) -> Page:
        """Get a new page instance."""
        return await self.browser.new_page()
        
    async def _safe_get_text(self, page: Page, selector: str) -> str:
        """Safely get text content from a selector."""
        try:
            element = await page.query_selector(selector)
            if element:
                return await element.text_content() or ""
            return ""
        except Exception as e:
            logger.warning(f"Failed to get text from selector {selector}: {e}")
            return ""
            
    async def _safe_get_attribute(self, page: Page, selector: str, attribute: str) -> str:
        """Safely get attribute value from a selector."""
        try:
            element = await page.query_selector(selector)
            if element:
                return await element.get_attribute(attribute) or ""
            return ""
        except Exception as e:
            logger.warning(f"Failed to get attribute {attribute} from selector {selector}: {e}")
            return ""
    
    async def search_hackathons(
        self, 
        search_url: Optional[str] = None,
        max_results: int = 10
    ) -> List[HackathonSearchResult]:
        """
        Search for hackathons based on criteria.
        
        Args:
            search_url: Custom search URL (uses default if None)
            max_results: Maximum number of results to return
            
        Returns:
            List of hackathon search results
        """
        if search_url is None:
            search_url = self.DEFAULT_SEARCH_URL
            
        logger.info(f"Searching hackathons: {search_url}")
        
        page = await self._get_page()
        
        try:
            # Set user agent
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            # Navigate to search page
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)  # Wait for dynamic content
            
            # Extract hackathon listings
            hackathons = []
            
            # Try different selectors for hackathon cards
            hackathon_selectors = [
                ".challenge-listing",
                ".hackathon-tile", 
                ".challenge-card",
                ".listing-item",
                ".hackathon-item"
            ]
            
            hackathon_elements = []
            for selector in hackathon_selectors:
                hackathon_elements = await page.query_selector_all(selector)
                if hackathon_elements:
                    logger.info(f"Found {len(hackathon_elements)} hackathons using selector: {selector}")
                    break
            
            if not hackathon_elements:
                logger.warning("No hackathon elements found. Trying fallback approach...")
                # Fallback: look for any links with '/hackathons/' or challenge URLs
                hackathon_elements = await page.query_selector_all("a[href*='/software/'], a[href*='.devpost.com']")
                
            for element in hackathon_elements[:max_results]:
                try:
                    # Extract hackathon information
                    name = await self._safe_get_text(element, "h3, h2, .challenge-title, .hackathon-title, .title")
                    
                    # Get hackathon URL
                    url = await self._safe_get_attribute(element, "a", "href")
                    if not url:
                        url = await element.get_attribute("href") or ""
                    
                    # Make URL absolute
                    if url.startswith("/"):
                        url = urljoin("https://devpost.com", url)
                    
                    # Skip if it's not a hackathon URL
                    if not url or "/software/" in url:
                        continue
                        
                    # Extract additional information
                    deadline_text = await self._safe_get_text(element, ".deadline, .date, .challenge-deadline")
                    participants_text = await self._safe_get_text(element, ".participants, .submissions")
                    prizes_text = await self._safe_get_text(element, ".prizes, .prize-amount")
                    description = await self._safe_get_text(element, ".description, .challenge-description")
                    
                    # Parse participants count
                    participants = None
                    if participants_text:
                        try:
                            import re
                            participant_match = re.search(r'(\d+)', participants_text.replace(',', ''))
                            if participant_match:
                                participants = int(participant_match.group(1))
                        except:
                            pass
                    
                    if name and url:
                        hackathon = HackathonSearchResult(
                            name=name.strip(),
                            url=url,
                            participants=participants,
                            prizes=prizes_text.strip() if prizes_text else None,
                            description=description.strip() if description else None
                        )
                        hackathons.append(hackathon)
                        logger.info(f"Found hackathon: {hackathon.name}")
                        
                except Exception as e:
                    logger.warning(f"Error extracting hackathon data: {e}")
                    continue
            
            await page.close()
            return hackathons
            
        except Exception as e:
            logger.error(f"Error searching hackathons: {e}")
            await page.close()
            return []
    
    async def find_recent_ai_hackathons(self, limit: int = 5) -> List[HackathonSearchResult]:
        """
        Find recent AI-related hackathons.
        
        Args:
            limit: Maximum number of hackathons to return
            
        Returns:
            List of recent AI hackathon search results
        """
        return await self.search_hackathons(max_results=limit)
    
    async def get_hackathon_project_gallery_url(self, hackathon_url: str) -> Optional[str]:
        """
        Get the project gallery URL for a hackathon.
        
        Args:
            hackathon_url: Main hackathon URL
            
        Returns:
            Project gallery URL if found, None otherwise
        """
        logger.info(f"Finding project gallery for: {hackathon_url}")
        
        page = await self._get_page()
        
        try:
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            await page.goto(hackathon_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)
            
            # Look for project gallery link
            gallery_selectors = [
                "a[href*='project-gallery']",
                "a[href*='submissions']", 
                "a[href*='projects']",
                "a:has-text('Gallery')",
                "a:has-text('Projects')",
                "a:has-text('Submissions')"
            ]
            
            for selector in gallery_selectors:
                gallery_link = await self._safe_get_attribute(page, selector, "href")
                if gallery_link:
                    if gallery_link.startswith("/"):
                        gallery_link = urljoin(hackathon_url, gallery_link)
                    await page.close()
                    return gallery_link
            
            # Fallback: try constructing the URL
            if hackathon_url.endswith("/"):
                hackathon_url = hackathon_url[:-1]
            
            potential_gallery_url = f"{hackathon_url}/project-gallery"
            
            await page.close()
            return potential_gallery_url
            
        except Exception as e:
            logger.error(f"Error finding project gallery: {e}")
            await page.close()
            return None


async def main():
    """Test function for hackathon search."""
    from scraper.devpost_scraper import DevpostScraper
    
    async with DevpostScraper() as scraper:
        searcher = HackathonSearcher(scraper.browser)
        
        # Search for recent AI hackathons
        hackathons = await searcher.find_recent_ai_hackathons(limit=5)
        
        print(f"Found {len(hackathons)} hackathons:")
        for i, hackathon in enumerate(hackathons, 1):
            print(f"{i}. {hackathon.name}")
            print(f"   URL: {hackathon.url}")
            print(f"   Participants: {hackathon.participants}")
            print(f"   Prizes: {hackathon.prizes}")
            print()


if __name__ == "__main__":
    import sys
    sys.path.append("..")
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())