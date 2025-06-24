#!/usr/bin/env python3
"""
Hackathon Insight Automator - Main CLI interface.

Usage:
    python src/main.py <devpost_url> [options]
"""
import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from dotenv import load_dotenv

from scraper.devpost_scraper import DevpostScraper
from scraper.hackathon_search import HackathonSearcher, LLMHackathonSelector
from report.markdown_generator import MarkdownReportGenerator
from models.hackathon import ScrapingResult

# Load environment variables
load_dotenv()

console = Console()


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )


def create_output_filename(url: str, base_dir: Path) -> Path:
    """Create output filename based on URL and timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Extract domain and path for filename
    if "/software/" in url:
        filename = f"project_{timestamp}"
    else:
        filename = f"hackathon_{timestamp}"
    
    return base_dir / f"{filename}.json"


def create_report_filename(hackathon_name: str, reports_dir: Path) -> Path:
    """Create report filename based on hackathon name."""
    safe_name = "".join(c for c in hackathon_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_name = safe_name.replace(' ', '_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return reports_dir / f"{safe_name}_{timestamp}.md"


async def search_and_select_hackathon(scraper: DevpostScraper, auto_select: bool = False) -> Optional[str]:
    """
    Search for recent AI hackathons and let user select one.
    
    Args:
        scraper: DevpostScraper instance with active browser
        auto_select: Whether to use LLM to automatically select hackathon
        
    Returns:
        Selected hackathon project gallery URL, or None if cancelled
    """
    logger = logging.getLogger(__name__)
    
    try:
        if not scraper.browser:
            logger.error("Browser not available for hackathon search")
            return None
        searcher = HackathonSearcher(scraper.browser)
        
        console.print("[blue]Searching for recent AI hackathons...[/blue]")
        hackathons = await searcher.find_recent_ai_hackathons(limit=10)
        
        if not hackathons:
            console.print("[red]No hackathons found.[/red]")
            return None
        
        # Display hackathons in a table
        table = Table(title="Recent AI Hackathons")
        table.add_column("No.", style="cyan", width=4)
        table.add_column("Name", style="green", min_width=30)
        table.add_column("Participants", style="magenta", width=12)
        table.add_column("URL", style="blue", overflow="fold")
        
        for i, hackathon in enumerate(hackathons, 1):
            participants = str(hackathon.participants) if hackathon.participants else "N/A"
            table.add_row(str(i), hackathon.name, participants, hackathon.url)
        
        console.print(table)
        
        # Use LLM for automatic selection if enabled
        if auto_select:
            console.print("\n[blue]Using AI to select the best hackathon...[/blue]")
            
            selector = LLMHackathonSelector()
            selected_hackathon, reasoning = await selector.select_best_hackathon(hackathons)
            
            if selected_hackathon:
                console.print(reasoning)
                
                # Construct project gallery URL
                hackathon_url = selected_hackathon.url
                
                # Clean up URL parameters and fragments
                from urllib.parse import urlparse, urlunparse
                parsed_url = urlparse(hackathon_url)
                # Keep only scheme, netloc, and path, remove query and fragment
                clean_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))
                
                if clean_url.endswith('/'):
                    clean_url = clean_url[:-1]
                
                gallery_url = f"{clean_url}/project-gallery"
                
                console.print(f"\n[green]✓ AI Selected:[/green] {selected_hackathon.name}")
                console.print(f"[blue]Gallery URL:[/blue] {gallery_url}")
                
                # Ask for confirmation
                confirm = input("\nProceed with this selection? (Y/n): ").strip().lower()
                if confirm == '' or confirm == 'y':
                    return gallery_url
                else:
                    console.print("[yellow]Selection cancelled. Please select manually.[/yellow]")
                    auto_select = False  # Fall back to manual selection
            else:
                console.print("[red]AI selection failed. Please select manually.[/red]")
                auto_select = False
        
        # Manual selection
        if not auto_select:
            while True:
                try:
                    selection = input(f"\nSelect hackathon (1-{len(hackathons)}) or 'q' to quit: ").strip()
                    
                    if selection.lower() == 'q':
                        return None
                    
                    idx = int(selection) - 1
                    if 0 <= idx < len(hackathons):
                        selected_hackathon = hackathons[idx]
                        
                        # Construct project gallery URL
                        hackathon_url = selected_hackathon.url
                        
                        # Clean up URL parameters and fragments
                        from urllib.parse import urlparse, urlunparse
                        parsed_url = urlparse(hackathon_url)
                        # Keep only scheme, netloc, and path, remove query and fragment
                        clean_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))
                        
                        if clean_url.endswith('/'):
                            clean_url = clean_url[:-1]
                        
                        gallery_url = f"{clean_url}/project-gallery"
                        
                        console.print(f"[green]Selected:[/green] {selected_hackathon.name}")
                        console.print(f"[blue]Gallery URL:[/blue] {gallery_url}")
                        
                        return gallery_url
                    else:
                        console.print("[red]Invalid selection. Please try again.[/red]")
                        
                except ValueError:
                    console.print("[red]Please enter a valid number or 'q' to quit.[/red]")
                except KeyboardInterrupt:
                    console.print("\n[yellow]Selection cancelled.[/yellow]")
                    return None
                
    except Exception as e:
        logger.error(f"Error during hackathon search: {e}")
        console.print(f"[red]Search failed:[/red] {e}")
        return None


async def scrape_and_analyze(
    url: Optional[str],
    output_dir: Path,
    reports_dir: Path,
    headless: bool = True,
    delay: float = 2.0,
    search_mode: bool = False,
    enable_llm: bool = True,
    auto_select: bool = False,
    generate_ideas: bool = False
) -> bool:
    """
    Main function to scrape and analyze hackathon data.
    
    Args:
        url: URL to scrape (can be None if search_mode is True)
        output_dir: Directory to save raw data
        reports_dir: Directory to save reports
        headless: Whether to run browser in headless mode
        delay: Delay between requests
        search_mode: Whether to search for hackathons instead of using provided URL
        enable_llm: Whether to enable LLM analysis for enhanced descriptions
        auto_select: Whether to use LLM to automatically select hackathon
        generate_ideas: Whether to generate AI ideas from the analysis
        
    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Create output directories
        output_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        async with DevpostScraper(headless=headless, delay=delay, enable_llm=enable_llm) as scraper:
            
            # Search mode: let user select a hackathon
            if search_mode:
                url = await search_and_select_hackathon(scraper, auto_select=auto_select)
                if not url:
                    console.print("[yellow]No hackathon selected. Exiting.[/yellow]")
                    return False
            
            # Validate URL
            if not url:
                console.print("[red]No URL provided.[/red]")
                return False
                
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                # Scraping phase
                scrape_task = progress.add_task("Scraping data from Devpost...", total=None)
                
                if "/software/" in url:
                    console.print(f"[blue]Scraping project:[/blue] {url}")
                    result = await scraper.scrape_project(url)
                else:
                    console.print(f"[blue]Scraping hackathon:[/blue] {url}")
                    result = await scraper.scrape_hackathon(url)
                
                # Save raw data
                output_file = create_output_filename(url, output_dir)
                scraper.save_result(result, output_file)
                
                progress.update(scrape_task, completed=True)
            
            if not result.success:
                console.print(f"[red]Scraping failed:[/red] {result.error_message}")
                return False
            
            if not result.hackathon:
                console.print("[red]No hackathon data found[/red]")
                return False
            
            # Report generation phase
            report_task = progress.add_task("Generating report...", total=None)
            
            generator = MarkdownReportGenerator()
            report_file = create_report_filename(result.hackathon.name, reports_dir)
            
            if generator.generate_report(result.hackathon, report_file, generate_ideas=generate_ideas):
                progress.update(report_task, completed=True)
                console.print(f"[green]Report generated:[/green] {report_file}")
                
                if generate_ideas:
                    console.print("[green]✓ AI-generated ideas included in report[/green]")
            else:
                console.print("[red]Failed to generate report[/red]")
                return False
        
        # Display summary
        display_summary(result)
        
        return True
        
    except Exception as e:
        logger.error(f"Error during scraping and analysis: {e}")
        return False


def display_summary(result: ScrapingResult) -> None:
    """Display a summary of the scraping results."""
    if not result.hackathon:
        return
    
    hackathon = result.hackathon
    
    # Create summary table
    table = Table(title=f"Analysis Summary: {hackathon.name}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Total Projects", str(len(hackathon.projects)))
    table.add_row("Scraped At", hackathon.scraped_at.strftime("%Y-%m-%d %H:%M:%S"))
    
    # Count technologies
    all_tags = []
    for project in hackathon.projects:
        all_tags.extend(project.tags)
    
    table.add_row("Unique Technologies", str(len(set(all_tags))))
    table.add_row("Total Technology Tags", str(len(all_tags)))
    
    # Count awards
    total_awards = sum(len(project.awards) for project in hackathon.projects)
    table.add_row("Total Awards", str(total_awards))
    
    console.print(table)
    
    # Show top technologies
    if all_tags:
        from collections import Counter
        tag_counter = Counter(all_tags)
        top_tags = tag_counter.most_common(5)
        
        console.print("\n[bold]Top Technologies:[/bold]")
        for i, (tag, count) in enumerate(top_tags, 1):
            console.print(f"{i}. {tag}: {count} project(s)")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Hackathon Insight Automator - Scrape and analyze hackathon data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Scrape a single project
    python src/main.py https://devpost.com/software/example-project

    # Scrape a hackathon
    python src/main.py https://example-hackathon.devpost.com

    # Run with custom settings
    python src/main.py https://devpost.com/software/example --no-headless --delay 3
        """
    )
    
    parser.add_argument(
        "url",
        nargs="?",
        help="Devpost URL to scrape (hackathon or project). Optional if using --search mode."
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory to save raw data (default: data/raw)"
    )
    
    parser.add_argument(
        "--reports-dir", 
        type=Path,
        default=Path("reports"),
        help="Directory to save reports (default: reports)"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (invisible)"
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        default=float(os.getenv("SCRAPING_DELAY", "2.0")),
        help="Delay between requests in seconds (default: 2.0)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--search",
        action="store_true",
        help="Search for recent AI hackathons instead of providing URL"
    )
    
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM analysis for project descriptions"
    )
    
    parser.add_argument(
        "--auto-select",
        action="store_true",
        help="Use AI to automatically select the best hackathon"
    )
    
    parser.add_argument(
        "--generate-ideas",
        action="store_true",
        help="Generate AI ideas based on hackathon trends"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Validate URL (only if not in search mode)
    if not args.search:
        if not args.url:
            console.print("[red]Error:[/red] URL is required when not using --search mode")
            sys.exit(1)
        if "devpost.com" not in args.url:
            console.print("[red]Error:[/red] URL must be from devpost.com")
            sys.exit(1)
    
    # Display startup info
    console.print("[bold green]Hackathon Insight Automator[/bold green]")
    if args.search:
        console.print("Mode: Search for recent AI hackathons")
    else:
        console.print(f"Target URL: {args.url}")
    console.print(f"Output directory: {args.output_dir}")
    console.print(f"Reports directory: {args.reports_dir}")
    console.print(f"Headless mode: {args.headless}")
    console.print(f"Request delay: {args.delay}s")
    console.print(f"LLM analysis: {'Disabled' if args.no_llm else 'Enabled'}")
    if args.auto_select:
        console.print("Auto-select mode: AI will select hackathon")
    if args.generate_ideas:
        console.print("Idea generation: AI will generate MVP ideas")
    console.print()
    
    # Run the scraper
    try:
        success = asyncio.run(scrape_and_analyze(
            args.url,
            args.output_dir,
            args.reports_dir,
            headless=args.headless,
            delay=args.delay,
            search_mode=args.search,
            enable_llm=not args.no_llm,
            auto_select=args.auto_select,
            generate_ideas=args.generate_ideas
        ))
        
        if success:
            console.print("[bold green]✓ Analysis completed successfully![/bold green]")
            sys.exit(0)
        else:
            console.print("[bold red]✗ Analysis failed[/bold red]")
            sys.exit(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()