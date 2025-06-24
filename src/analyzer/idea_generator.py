"""
AI idea generator for creating MVP ideas based on hackathon trends.
"""
import logging
import os
import json
from typing import List, Dict, Any, Optional
from collections import Counter

import google.generativeai as genai
from dotenv import load_dotenv

from models.hackathon import Hackathon, Project

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class IdeaGenerator:
    """Generates MVP ideas based on hackathon project analysis."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the idea generator.
        
        Args:
            api_key: Google API key (optional, will use env var if not provided)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            logger.warning("No Google API key found. Idea generation will be disabled.")
            self.enabled = False
            return
            
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.enabled = True
            logger.info("Idea generator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize idea generator: {e}")
            self.enabled = False
    
    def analyze_trends(self, hackathon: Hackathon) -> Dict[str, Any]:
        """
        Analyze trends from hackathon projects.
        
        Args:
            hackathon: Hackathon data with projects
            
        Returns:
            Dictionary containing trend analysis
        """
        # Extract all technologies
        all_technologies = []
        all_categories = []
        problem_domains = []
        
        for project in hackathon.projects:
            all_technologies.extend(project.tags)
            
            # Extract categories from description if available
            if project.description:
                desc_lower = project.description.lower()
                
                # Common problem domains
                domains = {
                    'healthcare': ['health', 'medical', 'patient', 'doctor', 'hospital', 'therapy'],
                    'education': ['education', 'learning', 'student', 'teacher', 'school', 'course'],
                    'finance': ['finance', 'banking', 'payment', 'money', 'investment', 'crypto'],
                    'environment': ['environment', 'climate', 'sustainable', 'green', 'carbon', 'energy'],
                    'accessibility': ['accessibility', 'disability', 'inclusive', 'blind', 'deaf'],
                    'mental_health': ['mental health', 'anxiety', 'depression', 'wellness', 'mindfulness'],
                    'productivity': ['productivity', 'efficiency', 'workflow', 'automation', 'task'],
                    'social': ['social', 'community', 'connect', 'network', 'communication']
                }
                
                for domain, keywords in domains.items():
                    if any(keyword in desc_lower for keyword in keywords):
                        problem_domains.append(domain)
        
        # Count frequencies
        tech_counter = Counter(all_technologies)
        domain_counter = Counter(problem_domains)
        
        # Get top items
        top_technologies = tech_counter.most_common(10)
        top_domains = domain_counter.most_common(5)
        
        # Identify technology combinations
        tech_combinations = []
        for project in hackathon.projects:
            if len(project.tags) >= 2:
                # Create pairs of technologies
                for i in range(len(project.tags)):
                    for j in range(i + 1, len(project.tags)):
                        tech_combinations.append((project.tags[i], project.tags[j]))
        
        combo_counter = Counter(tech_combinations)
        top_combinations = combo_counter.most_common(5)
        
        return {
            'top_technologies': top_technologies,
            'top_domains': top_domains,
            'tech_combinations': top_combinations,
            'total_projects': len(hackathon.projects),
            'unique_technologies': len(tech_counter)
        }
    
    async def generate_ideas(self, hackathon: Hackathon, num_ideas: int = 5) -> List[Dict[str, Any]]:
        """
        Generate MVP ideas based on hackathon trends.
        
        Args:
            hackathon: Hackathon data with projects
            num_ideas: Number of ideas to generate
            
        Returns:
            List of generated ideas
        """
        if not self.enabled:
            logger.warning("Idea generator is disabled")
            return []
        
        try:
            # Analyze trends
            trends = self.analyze_trends(hackathon)
            
            # Prepare project summaries
            project_summaries = []
            for project in hackathon.projects[:10]:  # Limit to top 10 projects
                summary = {
                    'name': project.name,
                    'technologies': project.tags,
                    'description': project.description[:200] if project.description else 'No description'
                }
                project_summaries.append(summary)
            
            # Create prompt
            prompt = f"""
Based on the analysis of {hackathon.name} with {trends['total_projects']} projects, generate {num_ideas} innovative MVP ideas.

TREND ANALYSIS:
- Top Technologies: {', '.join([f"{tech[0]} ({tech[1]})" for tech in trends['top_technologies'][:5]])}
- Top Problem Domains: {', '.join([f"{domain[0]} ({domain[1]})" for domain in trends['top_domains']])}
- Popular Tech Combinations: {', '.join([f"{combo[0][0]}+{combo[0][1]}" for combo in trends['tech_combinations'][:3]])}

SAMPLE WINNING PROJECTS:
{json.dumps(project_summaries[:5], indent=2)}

Generate {num_ideas} NEW MVP ideas that:
1. Combine trending technologies in novel ways
2. Address underserved problem areas
3. Have clear commercial potential
4. Are technically feasible for a hackathon team
5. Leverage AI/ML capabilities innovatively

For each idea, provide a JSON response with this structure:
{{
    "ideas": [
        {{
            "name": "Catchy project name",
            "tagline": "One-line description",
            "description": "2-3 sentence detailed description",
            "problem_statement": "Specific problem being solved",
            "target_users": "Primary user demographic",
            "key_features": ["Feature 1", "Feature 2", "Feature 3"],
            "tech_stack": ["Technology 1", "Technology 2", "etc"],
            "revenue_model": "How it could make money",
            "mvp_scope": "What can be built in 24-48 hours",
            "unique_value": "What makes this different",
            "market_size": "Potential market assessment",
            "implementation_steps": ["Step 1", "Step 2", "Step 3"],
            "potential_challenges": ["Challenge 1", "Challenge 2"],
            "growth_potential": "How it could scale",
            "ai_integration": "How AI/ML enhances the solution"
        }}
    ]
}}

Be creative but realistic. Focus on ideas that haven't been done in this hackathon.
Only return valid JSON, no additional text.
"""
            
            # Generate ideas
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                # Parse response
                response_text = response.text.strip()
                logger.debug(f"Raw idea generation response: {response_text[:500]}...")
                
                # Extract JSON
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    ideas_data = json.loads(json_match.group(0))
                    ideas = ideas_data.get('ideas', [])
                    
                    logger.info(f"Successfully generated {len(ideas)} MVP ideas")
                    return ideas
                else:
                    logger.error("Failed to extract JSON from idea generation response")
                    return []
            
        except Exception as e:
            logger.error(f"Error generating ideas: {e}")
            return []
    
    def format_ideas_markdown(self, ideas: List[Dict[str, Any]]) -> str:
        """
        Format generated ideas as markdown.
        
        Args:
            ideas: List of idea dictionaries
            
        Returns:
            Formatted markdown string
        """
        if not ideas:
            return "No ideas generated."
        
        markdown_parts = ["## 🚀 AI-Generated MVP Ideas\n"]
        markdown_parts.append("Based on the analysis of winning projects and emerging trends, here are innovative MVP ideas:\n")
        
        for i, idea in enumerate(ideas, 1):
            markdown_parts.append(f"### {i}. {idea.get('name', 'Untitled Idea')}")
            markdown_parts.append(f"**{idea.get('tagline', '')}**\n")
            
            if 'description' in idea:
                markdown_parts.append(f"**Description**: {idea['description']}\n")
            
            if 'problem_statement' in idea:
                markdown_parts.append(f"**Problem**: {idea['problem_statement']}\n")
            
            if 'target_users' in idea:
                markdown_parts.append(f"**Target Users**: {idea['target_users']}\n")
            
            if 'key_features' in idea and idea['key_features']:
                markdown_parts.append("**Key Features**:")
                for feature in idea['key_features']:
                    markdown_parts.append(f"- {feature}")
                markdown_parts.append("")
            
            if 'tech_stack' in idea and idea['tech_stack']:
                tech_list = ', '.join(idea['tech_stack'])
                markdown_parts.append(f"**Tech Stack**: {tech_list}\n")
            
            if 'ai_integration' in idea:
                markdown_parts.append(f"**AI Integration**: {idea['ai_integration']}\n")
            
            if 'mvp_scope' in idea:
                markdown_parts.append(f"**MVP Scope**: {idea['mvp_scope']}\n")
            
            if 'revenue_model' in idea:
                markdown_parts.append(f"**Revenue Model**: {idea['revenue_model']}\n")
            
            if 'unique_value' in idea:
                markdown_parts.append(f"**Unique Value**: {idea['unique_value']}\n")
            
            if 'implementation_steps' in idea and idea['implementation_steps']:
                markdown_parts.append("**Implementation Steps**:")
                for j, step in enumerate(idea['implementation_steps'], 1):
                    markdown_parts.append(f"{j}. {step}")
                markdown_parts.append("")
            
            if 'growth_potential' in idea:
                markdown_parts.append(f"**Growth Potential**: {idea['growth_potential']}\n")
            
            markdown_parts.append("---\n")
        
        return '\n'.join(markdown_parts)


async def main():
    """Test function for idea generator."""
    import asyncio
    import sys
    sys.path.append("..")
    
    # Create a sample hackathon with projects
    from models.hackathon import Hackathon, Project
    
    sample_projects = [
        Project(
            name="AI Health Assistant",
            description="AI-powered health monitoring app",
            devpost_url="https://example.com",
            tags=["python", "tensorflow", "react", "firebase"]
        ),
        Project(
            name="EcoTracker",
            description="Carbon footprint tracking application",
            devpost_url="https://example.com",
            tags=["javascript", "node.js", "mongodb", "react"]
        )
    ]
    
    hackathon = Hackathon(
        name="Test Hackathon",
        devpost_url="https://example.com",
        projects=sample_projects
    )
    
    generator = IdeaGenerator()
    ideas = await generator.generate_ideas(hackathon, num_ideas=3)
    
    if ideas:
        markdown = generator.format_ideas_markdown(ideas)
        print(markdown)
    else:
        print("No ideas generated")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())