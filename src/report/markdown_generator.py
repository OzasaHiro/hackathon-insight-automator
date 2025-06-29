"""
Markdown report generator for hackathon analysis.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from jinja2 import Environment, FileSystemLoader, Template
from collections import Counter

from models.hackathon import Hackathon, Project, ScrapingResult
from analyzer.idea_generator import IdeaGenerator

logger = logging.getLogger(__name__)


class MarkdownReportGenerator:
    """Generates Markdown reports from hackathon data."""
    
    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize the report generator.
        
        Args:
            template_dir: Directory containing Jinja2 templates
        """
        if template_dir and template_dir.exists():
            self.env = Environment(loader=FileSystemLoader(template_dir))
        else:
            # Use string templates if no template directory is provided
            self.env = Environment(loader=None)
        
    def _create_default_template(self) -> Template:
        """Create a default template for hackathon reports."""
        template_str = """# {{ hackathon.name }} - Analysis Report

Generated on: {{ generation_date }}

## Overview
- **Event**: {{ hackathon.name }}
- **URL**: {{ hackathon.devpost_url }}
- **Total Projects**: {{ hackathon.projects|length }}
- **Analysis Date**: {{ hackathon.scraped_at.strftime('%Y-%m-%d %H:%M:%S') if hackathon.scraped_at else 'N/A' }}
{%- if hackathon.description %}

### Description
{{ hackathon.description }}
{%- endif %}

## Project Statistics

### Top Technologies/Tags
{%- for tag, count in top_tags %}
- **{{ tag }}**: {{ count }} project(s)
{%- endfor %}
{%- if award_distribution %}

### Award Distribution
{%- for award, count in award_distribution %}
- **{{ award }}**: {{ count }} project(s)
{%- endfor %}
{%- endif %}

## Projects
{%- for project in hackathon.projects %}

### {{ project.name }}
{%- if project.description %}

{{ project.description }}
{%- else %}

**Description**: No description available
{%- endif %}

**Technologies**: {% for tag in project.tags %}{{ tag }}{% if not loop.last %}, {% endif %}{% endfor %}
{%- if project.awards %}

**Awards**: {% for award in project.awards %}{{ award.name }}{% if not loop.last %}, {% endif %}{% endfor %}
{%- endif %}
{%- if project.members %}

**Team**: {% for member in project.members %}{{ member.name }}{% if not loop.last %}, {% endif %}{% endfor %}
{%- endif %}

**Project URL**: {{ project.devpost_url }}
{%- if project.project_url %}
**External URL**: {{ project.project_url }}
{%- endif %}
{%- if not loop.last %}

---
{%- endif %}
{%- endfor %}

## Analysis Summary

This report analyzed {{ hackathon.projects|length }} projects from {{ hackathon.name }}.
{%- if top_tags %}

The most popular technologies were:
{%- for tag, count in top_tags[:3] %}
{{ loop.index }}. {{ tag }} ({{ count }} projects)
{%- endfor %}
{%- endif %}

## Methodology

This report was generated by scraping data from Devpost using automated tools. The analysis includes project descriptions, technologies used, team information, and awards received.
{%- if include_ideas and ai_ideas %}

---

{{ ai_ideas }}
{%- endif %}

---

*Report generated by Hackathon Insight Automator on {{ generation_date }}*
"""
        return self.env.from_string(template_str)
    
    def _analyze_hackathon_data(self, hackathon: Hackathon) -> Dict[str, Any]:
        """
        Analyze hackathon data to extract insights.
        
        Args:
            hackathon: Hackathon data to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        projects = hackathon.projects
        
        # Count technologies/tags
        all_tags = []
        for project in projects:
            all_tags.extend(project.tags)
        
        tag_counter = Counter(all_tags)
        top_tags = tag_counter.most_common(10)
        
        # Count awards
        all_awards = []
        for project in projects:
            for award in project.awards:
                all_awards.append(award.name)
        
        award_counter = Counter(all_awards)
        award_distribution = award_counter.most_common(10)
        
        # Team size analysis
        team_sizes = []
        for project in projects:
            team_sizes.append(len(project.members))
        
        avg_team_size = sum(team_sizes) / len(team_sizes) if team_sizes else 0
        
        return {
            'top_tags': top_tags,
            'award_distribution': award_distribution,
            'avg_team_size': round(avg_team_size, 1),
            'total_projects': len(projects),
            'total_awards': len(all_awards),
            'unique_technologies': len(tag_counter)
        }
    
    def generate_report(
        self, 
        hackathon: Hackathon, 
        output_path: Path,
        template_name: Optional[str] = None,
        generate_ideas: bool = False
    ) -> bool:
        """
        Generate a Markdown report for a hackathon.
        
        Args:
            hackathon: Hackathon data to generate report for
            output_path: Path to save the report
            template_name: Name of template file to use (optional)
            generate_ideas: Whether to generate AI ideas
            
        Returns:
            True if report was generated successfully, False otherwise
        """
        try:
            # Get template
            if template_name:
                try:
                    template = self.env.get_template(template_name)
                except:
                    logger.warning(f"Template {template_name} not found, using default")
                    template = self._create_default_template()
            else:
                template = self._create_default_template()
            
            # Analyze data
            analysis = self._analyze_hackathon_data(hackathon)
            
            # Generate AI ideas if requested
            ideas_markdown = ""
            if generate_ideas:
                try:
                    logger.info("Generating AI ideas...")
                    idea_generator = IdeaGenerator()
                    
                    if not idea_generator.enabled:
                        ideas_markdown = "## 🚀 AI-Generated MVP Ideas\n\n⚠️ AI idea generation is disabled. Please ensure your Google API key is set in the environment variables."
                    else:
                        # Call synchronous function directly
                        ideas = idea_generator.generate_ideas(hackathon, num_ideas=5)
                        
                        if ideas:
                            ideas_markdown = idea_generator.format_ideas_markdown(ideas)
                            logger.info(f"Generated {len(ideas)} AI ideas")
                        else:
                            logger.warning("No AI ideas generated")
                            ideas_markdown = "## 🚀 AI-Generated MVP Ideas\n\n⚠️ Unable to generate ideas. This may be due to:\n- Insufficient project data\n- API rate limits\n- Network connectivity issues\n\nPlease try again later."
                except Exception as e:
                    logger.error(f"Error generating AI ideas: {e}", exc_info=True)
                    ideas_markdown = f"## 🚀 AI-Generated MVP Ideas\n\n⚠️ Error generating ideas: {str(e)}\n\nPlease check:\n- Google API key is correctly set\n- Network connectivity\n- API quota limits"
            
            # Prepare template context
            context = {
                'hackathon': hackathon,
                'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'ai_ideas': ideas_markdown,
                'include_ideas': generate_ideas,
                **analysis
            }
            
            # Generate report
            report_content = template.render(**context)
            
            # Save report
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"Generated report: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return False
    
    def generate_summary_report(
        self, 
        results: List[ScrapingResult], 
        output_path: Path
    ) -> bool:
        """
        Generate a summary report from multiple scraping results.
        
        Args:
            results: List of scraping results
            output_path: Path to save the summary report
            
        Returns:
            True if report was generated successfully, False otherwise
        """
        try:
            successful_results = [r for r in results if r.success and r.hackathon]
            
            if not successful_results:
                logger.error("No successful scraping results to generate summary")
                return False
            
            # Combine all projects
            all_projects = []
            hackathon_names = []
            
            for result in successful_results:
                hackathon = result.hackathon
                all_projects.extend(hackathon.projects)
                hackathon_names.append(hackathon.name)
            
            # Create combined hackathon for analysis
            combined_hackathon = Hackathon(
                name=f"Combined Analysis ({len(hackathon_names)} events)",
                devpost_url="https://devpost.com",
                projects=all_projects
            )
            
            # Generate report
            return self.generate_report(combined_hackathon, output_path)
            
        except Exception as e:
            logger.error(f"Failed to generate summary report: {e}")
            return False


def main():
    """Main function for testing the report generator."""
    import json
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python markdown_generator.py <json_data_file>")
        return
    
    data_file = Path(sys.argv[1])
    
    if not data_file.exists():
        print(f"Data file not found: {data_file}")
        return
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Load data
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create ScrapingResult from JSON
        result = ScrapingResult(**data)
        
        if not result.success or not result.hackathon:
            print("No valid hackathon data found")
            return
        
        # Generate report
        generator = MarkdownReportGenerator()
        output_path = Path("reports") / f"{result.hackathon.name.replace(' ', '_')}_report.md"
        
        if generator.generate_report(result.hackathon, output_path):
            print(f"Report generated: {output_path}")
        else:
            print("Failed to generate report")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()