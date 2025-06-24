"""
Devpost scraper implementation using Playwright.
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Page, Browser
from pydantic import ValidationError

from models.hackathon import (
    Hackathon, Project, ProjectMember, Award, ScrapingResult
)
from analyzer.llm_analyzer import LLMAnalyzer

logger = logging.getLogger(__name__)


class DevpostScraper:
    """Scraper for Devpost hackathon and project data."""
    
    def __init__(self, headless: bool = True, delay: float = 2.0, enable_llm: bool = True):
        """
        Initialize the scraper.
        
        Args:
            headless: Whether to run browser in headless mode
            delay: Delay between requests in seconds
            enable_llm: Whether to enable LLM analysis for project descriptions
        """
        self.headless = headless
        self.delay = delay
        self.browser: Optional[Browser] = None
        self.enable_llm = enable_llm
        self.llm_analyzer = LLMAnalyzer() if enable_llm else None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.playwright = await async_playwright().start()
        
        # Try different browser launch options for macOS compatibility
        launch_options = {
            'headless': self.headless,
            'timeout': 60000,  # Increase timeout
        }
        
        if self.headless:
            # More conservative options for headless mode
            launch_options['args'] = [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--single-process',
                '--disable-gpu'
            ]
        
        try:
            self.browser = await self.playwright.chromium.launch(**launch_options)
        except Exception as e:
            logger.warning(f"Failed to launch Chromium: {e}")
            # Fallback to Firefox
            logger.info("Trying Firefox instead...")
            try:
                self.browser = await self.playwright.firefox.launch(
                    headless=self.headless,
                    timeout=60000
                )
            except Exception as e2:
                logger.error(f"Failed to launch Firefox: {e2}")
                # Last resort: try WebKit
                logger.info("Trying WebKit instead...")
                self.browser = await self.playwright.webkit.launch(
                    headless=self.headless,
                    timeout=60000
                )
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        try:
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")
        try:
            await self.playwright.stop()
        except Exception as e:
            logger.warning(f"Error stopping playwright: {e}")
        
    async def _get_page(self) -> Page:
        """Get a new page instance."""
        if not self.browser:
            raise RuntimeError("Browser not initialized. Use async context manager.")
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
            
    async def scrape_project(self, project_url: str) -> ScrapingResult:
        """
        Scrape a single project page.
        
        Args:
            project_url: URL of the project page
            
        Returns:
            ScrapingResult containing the scraped data
        """
        try:
            page = await self._get_page()
            
            logger.info(f"Scraping project: {project_url}")
            
            # Set user agent to avoid being blocked
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            # Navigate with timeout and proper wait
            await page.goto(project_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)  # Wait for dynamic content
            
            # Extract project information using updated selectors for Devpost
            project_name = await self._safe_get_text(page, "h1, #app-title, .software-header h1")
            
            # Get page HTML content for LLM analysis
            page_html = ""
            if self.enable_llm and self.llm_analyzer and self.llm_analyzer.enabled:
                try:
                    page_html = await page.content()
                except Exception as e:
                    logger.warning(f"Failed to get page HTML for LLM analysis: {e}")
            
            # Try multiple selectors for description
            description_selectors = [
                "#app-details-left .app-details-left",
                "#app-details-left",
                ".software-description",
                ".project-description", 
                "#app-description",
                "[data-field='description']",
                ".user-content",
                ".user_content",
                ".app-info",
                "article.software-details",
                ".software-details",
                ".details-content",
                "#gallery-item-description"
            ]
            description = ""
            for selector in description_selectors:
                elements = await page.query_selector_all(f"{selector} p")
                if elements:
                    texts = []
                    for element in elements[:5]:  # Get first 5 paragraphs
                        text = await element.text_content()
                        if text and text.strip():
                            texts.append(text.strip())
                    if texts:
                        description = " ".join(texts)
                        logger.info(f"Found description using selector: {selector}")
                        break
                
                # Try direct selector if paragraph approach fails
                if not description:
                    description = await self._safe_get_text(page, selector)
                    if description.strip():
                        logger.info(f"Found description using direct selector: {selector}")
                        break
            
            # Extract tags using updated selectors
            tags = []
            tag_selectors = [
                "#built-with a",
                ".software-tags a", 
                ".tags a",
                "#app-built-with a",
                "[data-field='built_with'] a"
            ]
            for selector in tag_selectors:
                tag_elements = await page.query_selector_all(selector)
                for tag_element in tag_elements:
                    tag_text = await tag_element.text_content()
                    if tag_text and tag_text.strip():
                        tags.append(tag_text.strip())
                if tags:  # If we found tags, don't try other selectors
                    break
            
            # Extract team members using updated selectors
            members = []
            member_selectors = [
                "#app-team .user-profile",
                ".software-team .member",
                ".team-members .member",
                "#software-team-members .user-profile"
            ]
            for selector in member_selectors:
                member_elements = await page.query_selector_all(selector)
                for member_element in member_elements:
                    member_name = await self._safe_get_text(member_element, "h4, .user-profile-name, .member-name")
                    profile_url = await self._safe_get_attribute(member_element, "a", "href")
                    
                    if member_name and member_name.strip():
                        member = ProjectMember(
                            name=member_name.strip(),
                            profile_url=profile_url if profile_url else None
                        )
                        members.append(member)
                if members:  # If we found members, don't try other selectors
                    break
            
            # Extract awards using updated selectors
            awards = []
            award_selectors = [
                ".software-winner",
                ".winner-badge",
                ".award-badge", 
                ".prize-badge",
                "#app-awards .award"
            ]
            for selector in award_selectors:
                award_elements = await page.query_selector_all(selector)
                for award_element in award_elements:
                    award_name = await award_element.text_content()
                    if award_name and award_name.strip():
                        award = Award(name=award_name.strip())
                        awards.append(award)
                if awards:  # If we found awards, don't try other selectors
                    break
            
            # Extract project URL using updated selectors
            project_link_selectors = [
                "a[href*='github.com']",
                "a[href*='gitlab.com']",
                "a[href*='bitbucket.com']",
                "#app-links a",
                ".software-links a"
            ]
            project_link = ""
            for selector in project_link_selectors:
                project_link = await self._safe_get_attribute(page, selector, "href")
                if project_link and not project_link.startswith("/"):
                    break
            
            # Log description status
            if description:
                logger.info(f"Found description for {project_name}: {len(description)} characters")
            else:
                logger.warning(f"No description found for {project_name}")
                # Try to get any text content from the page as fallback
                try:
                    fallback_selectors = [
                        "main", "article", ".container", "#content", "body"
                    ]
                    for selector in fallback_selectors:
                        fallback_text = await self._safe_get_text(page, selector)
                        if fallback_text and len(fallback_text) > 100:
                            # Extract first 500 characters of meaningful content
                            lines = fallback_text.split('\n')
                            meaningful_lines = [line.strip() for line in lines if len(line.strip()) > 20]
                            if meaningful_lines:
                                description = ' '.join(meaningful_lines[:5])[:500] + "..."
                                logger.info(f"Used fallback description from {selector}")
                                break
                except Exception as e:
                    logger.error(f"Failed to get fallback description: {e}")
            
            # Perform LLM analysis if enabled
            enhanced_description = description
            if (self.enable_llm and self.llm_analyzer and self.llm_analyzer.enabled 
                and page_html and project_name):
                try:
                    logger.info(f"Performing LLM analysis for project: {project_name}")
                    llm_analysis = await self.llm_analyzer.analyze_project_content(
                        page_html, project_name
                    )
                    if llm_analysis:
                        enhanced_description = self.llm_analyzer.create_enhanced_description(llm_analysis)
                        if enhanced_description:
                            # Combine original description with LLM analysis
                            if description:
                                enhanced_description = f"{description}\n\n---\n\n{enhanced_description}"
                        else:
                            enhanced_description = description
                        logger.info(f"LLM analysis completed for: {project_name}")
                    else:
                        logger.warning(f"No LLM analysis results for: {project_name}")
                except Exception as e:
                    logger.error(f"LLM analysis failed for {project_name}: {e}")
                    enhanced_description = description
            
            # Ensure we have at least some description
            if not enhanced_description:
                enhanced_description = f"Project: {project_name}. No detailed description available."
            
            # Create project object
            project = Project(
                name=project_name or "Unknown Project",
                description=enhanced_description or "",
                devpost_url=project_url,
                project_url=project_link if project_link else None,
                tags=tags,
                awards=awards,
                members=members
            )
            
            # Create a basic hackathon object (this is a simplified version)
            hackathon = Hackathon(
                name="Scraped Hackathon",
                devpost_url=project_url,
                projects=[project]
            )
            
            await page.close()
            await asyncio.sleep(self.delay)
            
            return ScrapingResult(
                success=True,
                url=project_url,
                hackathon=hackathon
            )
            
        except Exception as e:
            logger.error(f"Failed to scrape project {project_url}: {e}")
            return ScrapingResult(
                success=False,
                url=project_url,
                error_message=str(e)
            )
    
    async def scrape_hackathon(self, hackathon_url: str) -> ScrapingResult:
        """
        Scrape a hackathon page and its projects.
        
        Args:
            hackathon_url: URL of the hackathon page
            
        Returns:
            ScrapingResult containing the scraped data
        """
        try:
            page = await self._get_page()
            
            logger.info(f"Scraping hackathon: {hackathon_url}")
            
            # Set user agent to avoid being blocked
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            # Navigate with timeout and proper wait
            await page.goto(hackathon_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)  # Wait for dynamic content
            
            # Debug: Check if we're on the right page
            page_title = await page.title()
            logger.info(f"Page title: {page_title}")
            logger.info(f"Current URL: {page.url}")
            
            # Extract hackathon information using updated selectors
            hackathon_name = await self._safe_get_text(page, "h1, .header-title, .challenge-header h1, .hackathon-title")
            if not hackathon_name.strip():
                # Try extracting from page title
                hackathon_name = await page.title()
                if "Devpost" in hackathon_name:
                    hackathon_name = hackathon_name.replace(" | Devpost", "")
            
            description = await self._safe_get_text(page, ".hackathon-description, .challenge-description, .description, .header-description")
            
            # Extract project URLs using multiple selectors
            project_selectors = [
                "a[href*='/software/']",
                ".submission-item a",
                ".project-card a",
                ".challenge-submission a",
                ".software-entry a"
            ]
            
            project_links = []
            for selector in project_selectors:
                links = await page.query_selector_all(selector)
                if links:
                    logger.info(f"Found {len(links)} project links using selector: {selector}")
                    project_links.extend(links)
                    break
            
            if not project_links:
                logger.warning("No project links found. Trying fallback approach...")
                # Fallback: look for any software links on the page
                project_links = await page.query_selector_all("a[href*='devpost.com/software']")
            
            project_urls = []
            for link in project_links[:5]:  # Limit to first 5 projects for MVP
                href = await link.get_attribute("href")
                if href:
                    full_url = urljoin(hackathon_url, href)
                    if full_url not in project_urls and '/software/' in full_url:
                        project_urls.append(full_url)
                        logger.info(f"Added project URL: {full_url}")
            
            logger.info(f"Total project URLs found: {len(project_urls)}")
            
            await page.close()
            
            # Scrape individual projects
            projects = []
            for project_url in project_urls:
                project_result = await self.scrape_project(project_url)
                if project_result.success and project_result.hackathon:
                    projects.extend(project_result.hackathon.projects)
            
            # Create hackathon object
            hackathon = Hackathon(
                name=hackathon_name or "Unknown Hackathon",
                description=description,
                devpost_url=hackathon_url,
                projects=projects
            )
            
            return ScrapingResult(
                success=True,
                url=hackathon_url,
                hackathon=hackathon
            )
            
        except Exception as e:
            logger.error(f"Failed to scrape hackathon {hackathon_url}: {e}")
            return ScrapingResult(
                success=False,
                url=hackathon_url,
                error_message=str(e)
            )
    
    def save_result(self, result: ScrapingResult, output_path: Path) -> None:
        """
        Save scraping result to JSON file.
        
        Args:
            result: ScrapingResult to save
            output_path: Path to save the JSON file
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result.dict(), f, indent=2, ensure_ascii=False, default=str)
                
            logger.info(f"Saved scraping result to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save result to {output_path}: {e}")


async def main():
    """Main function for testing the scraper."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python devpost_scraper.py <devpost_url>")
        return
    
    url = sys.argv[1]
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    async with DevpostScraper() as scraper:
        if "/software/" in url:
            result = await scraper.scrape_project(url)
        else:
            result = await scraper.scrape_hackathon(url)
        
        output_path = Path("data/raw/scraped_data.json")
        scraper.save_result(result, output_path)
        
        if result.success:
            print(f"Successfully scraped: {url}")
            print(f"Data saved to: {output_path}")
        else:
            print(f"Failed to scrape: {url}")
            print(f"Error: {result.error_message}")


if __name__ == "__main__":
    asyncio.run(main())