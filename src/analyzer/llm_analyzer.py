"""
LLM analyzer for extracting and summarizing project descriptions.
"""
import logging
import os
import re
from typing import Optional, Dict, Any

import google.generativeai as genai
from dotenv import load_dotenv

# from models.hackathon import Project  # Currently unused

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """Analyzes project content using Google Gemini."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM analyzer.
        
        Args:
            api_key: Google API key (optional, will use env var if not provided)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            logger.warning("No Google API key found. LLM analysis will be disabled.")
            self.enabled = False
            return
            
        try:
            genai.configure(api_key=self.api_key)
            # Use the correct model name for Gemini
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.enabled = True
            logger.info("LLM analyzer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM analyzer: {e}")
            self.enabled = False
    
    def extract_project_sections(self, html_content: str) -> Dict[str, str]:
        """
        Extract project sections from HTML content.
        
        Args:
            html_content: Raw HTML content from project page
            
        Returns:
            Dictionary with section names and content
        """
        sections = {}
        
        # Common section patterns in Devpost projects
        section_patterns = [
            (r'<h2[^>]*>Inspiration</h2>\s*<p[^>]*>(.*?)</p>', 'inspiration'),
            (r'<h2[^>]*>What it does</h2>\s*<p[^>]*>(.*?)</p>', 'what_it_does'),
            (r'<h2[^>]*>How we built it</h2>\s*<p[^>]*>(.*?)</p>', 'how_built'),
            (r'<h2[^>]*>Challenges we ran into</h2>\s*<p[^>]*>(.*?)</p>', 'challenges'),
            (r'<h2[^>]*>Accomplishments that we\'re proud of</h2>\s*<p[^>]*>(.*?)</p>', 'accomplishments'),
            (r'<h2[^>]*>What we learned</h2>\s*<p[^>]*>(.*?)</p>', 'learned'),
            (r'<h2[^>]*>What\'s next for [^<]*</h2>\s*<p[^>]*>(.*?)</p>', 'whats_next'),
        ]
        
        for pattern, section_name in section_patterns:
            match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if match:
                # Clean up HTML tags and normalize whitespace
                content = re.sub(r'<[^>]+>', '', match.group(1))
                content = re.sub(r'\s+', ' ', content).strip()
                sections[section_name] = content
        
        return sections
    
    async def analyze_project_content(self, html_content: str, project_name: str) -> Dict[str, Any]:
        """
        Analyze project content using LLM.
        
        Args:
            html_content: Raw HTML content from project page
            project_name: Name of the project
            
        Returns:
            Dictionary with analysis results
        """
        if not self.enabled:
            logger.warning("LLM analyzer is disabled. Skipping analysis.")
            return {}
        
        try:
            # Extract sections first
            sections = self.extract_project_sections(html_content)
            
            if not sections:
                logger.warning(f"No project sections found for {project_name}")
                return {}
            
            # Create prompt for LLM analysis
            prompt = f"""
Analyze this hackathon project and provide a structured summary:

Project Name: {project_name}

Project Sections:
"""
            
            for section, content in sections.items():
                prompt += f"\n{section.replace('_', ' ').title()}: {content}\n"
            
            prompt += """
Please provide a comprehensive JSON analysis with the following structure:
{
    "summary": "A concise 2-3 sentence summary of what this project does",
    "detailed_description": "A detailed 4-5 sentence explanation of the project's functionality, architecture, and implementation approach",
    "key_technologies": ["list", "of", "main", "technologies", "used"],
    "technical_architecture": {
        "frontend": "Description of frontend stack and approach",
        "backend": "Description of backend services and APIs",
        "database": "Data storage and management approach",
        "deployment": "How the project is deployed/hosted",
        "external_services": ["List of external APIs or services used"]
    },
    "innovation_analysis": {
        "level": "high/medium/low",
        "novel_aspects": ["List of innovative features or approaches"],
        "technical_breakthroughs": "Any significant technical achievements",
        "unique_value_proposition": "What makes this different from existing solutions"
    },
    "market_analysis": {
        "problem_solved": "Detailed description of the problem being addressed",
        "target_audience": "Specific user segments and demographics",
        "market_size": "Potential market size assessment",
        "commercial_potential": "high/medium/low",
        "monetization_strategy": "Potential ways to monetize this solution",
        "competitors": ["List of potential competitors or similar solutions"],
        "competitive_advantages": ["Key differentiators from competitors"]
    },
    "implementation_quality": {
        "technical_complexity": "high/medium/low",
        "code_quality_indicators": ["Observable quality metrics like testing, documentation"],
        "scalability_considerations": "How well the solution could scale",
        "security_considerations": "Security measures and potential vulnerabilities"
    },
    "social_impact": {
        "level": "high/medium/low",
        "beneficiaries": "Who benefits from this solution",
        "potential_reach": "How many people could be impacted",
        "sustainability": "Long-term viability and impact"
    },
    "key_features": ["Comprehensive", "list", "of", "main", "features", "and", "capabilities"],
    "future_potential": {
        "growth_opportunities": ["Ways this project could expand"],
        "technical_improvements": ["Suggested technical enhancements"],
        "feature_roadmap": ["Potential future features"]
    },
    "categories": ["fintech", "healthtech", "edtech", "etc"],
    "overall_assessment": {
        "strengths": ["Key strengths of the project"],
        "weaknesses": ["Areas for improvement"],
        "opportunities": ["Market or technical opportunities"],
        "threats": ["Potential challenges or risks"]
    }
}

Provide a thorough, insightful analysis. Only return valid JSON, no additional text.
"""
            
            # Generate analysis
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                # Clean up response text
                response_text = response.text.strip()
                logger.debug(f"Raw LLM response: {response_text}")
                
                # Try to extract JSON from response (sometimes LLM includes extra text)
                import json
                import re
                
                # Look for JSON content in the response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)
                else:
                    json_text = response_text
                
                try:
                    analysis = json.loads(json_text)
                    analysis['sections'] = sections  # Include original sections
                    logger.info(f"Successfully analyzed project: {project_name}")
                    return analysis
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM response as JSON: {e}")
                    logger.debug(f"Response text: {response_text}")
                    
                    # Fallback: create basic analysis from sections
                    basic_analysis = {
                        'sections': sections,
                        'summary': sections.get('what_it_does', sections.get('inspiration', 'No summary available')),
                        'llm_raw_response': response_text,
                        'llm_analysis_error': f'JSON parsing failed: {str(e)}'
                    }
                    
                    # Extract some basic info if possible
                    if 'what_it_does' in sections:
                        basic_analysis['summary'] = sections['what_it_does']
                    if 'how_built' in sections:
                        # Try to extract technologies from "how we built it" section
                        tech_text = sections['how_built'].lower()
                        common_techs = ['react', 'python', 'javascript', 'node.js', 'flask', 'express', 'mongodb', 'postgresql', 'mysql', 'aws', 'firebase', 'docker']
                        found_techs = [tech for tech in common_techs if tech in tech_text]
                        if found_techs:
                            basic_analysis['key_technologies'] = found_techs
                    
                    return basic_analysis
            else:
                logger.error(f"Empty response from LLM for project: {project_name}")
                return {
                    'sections': sections,
                    'summary': sections.get('what_it_does', 'No summary available'),
                    'llm_analysis_error': 'Empty LLM response'
                }
                
        except Exception as e:
            logger.error(f"Error analyzing project {project_name}: {e}")
            return {}
    
    def create_enhanced_description(self, analysis: Dict[str, Any]) -> str:
        """
        Create an enhanced description from LLM analysis.
        
        Args:
            analysis: Analysis results from analyze_project_content
            
        Returns:
            Enhanced description string
        """
        if not analysis:
            return ""
        
        description_parts = []
        
        # Add summary and detailed description
        if 'summary' in analysis:
            description_parts.append(f"**Summary**: {analysis['summary']}")
        
        if 'detailed_description' in analysis:
            description_parts.append(f"**Detailed Description**: {analysis['detailed_description']}")
        
        # Add market analysis
        market = analysis.get('market_analysis', {})
        if market:
            if 'problem_solved' in market:
                description_parts.append(f"**Problem Addressed**: {market['problem_solved']}")
            if 'target_audience' in market:
                description_parts.append(f"**Target Audience**: {market['target_audience']}")
            if 'commercial_potential' in market:
                description_parts.append(f"**Commercial Potential**: {market['commercial_potential'].title()}")
        
        # Add innovation analysis
        innovation = analysis.get('innovation_analysis', {})
        if innovation:
            if 'level' in innovation:
                description_parts.append(f"**Innovation Level**: {innovation['level'].title()}")
            if 'unique_value_proposition' in innovation:
                description_parts.append(f"**Unique Value**: {innovation['unique_value_proposition']}")
        
        # Add technical architecture
        tech_arch = analysis.get('technical_architecture', {})
        if tech_arch:
            arch_parts = []
            for key, value in tech_arch.items():
                if value and not (isinstance(value, list) and len(value) == 0):
                    arch_parts.append(f"{key.title()}: {value}")
            if arch_parts:
                description_parts.append(f"**Technical Architecture**:\n" + '\n'.join(f"  - {part}" for part in arch_parts))
        
        # Add key features
        if 'key_features' in analysis and analysis['key_features']:
            features = '\n'.join(f"  - {feature}" for feature in analysis['key_features'])
            description_parts.append(f"**Key Features**:\n{features}")
        
        # Add implementation quality
        impl_quality = analysis.get('implementation_quality', {})
        if impl_quality:
            if 'technical_complexity' in impl_quality:
                description_parts.append(f"**Technical Complexity**: {impl_quality['technical_complexity'].title()}")
            if 'scalability_considerations' in impl_quality:
                description_parts.append(f"**Scalability**: {impl_quality['scalability_considerations']}")
        
        # Add social impact
        social = analysis.get('social_impact', {})
        if social:
            if 'level' in social:
                description_parts.append(f"**Social Impact**: {social['level'].title()}")
            if 'potential_reach' in social:
                description_parts.append(f"**Potential Reach**: {social['potential_reach']}")
        
        # Add overall assessment (SWOT)
        assessment = analysis.get('overall_assessment', {})
        if assessment:
            swot_parts = []
            for key in ['strengths', 'weaknesses', 'opportunities', 'threats']:
                if key in assessment and assessment[key]:
                    items = '\n'.join(f"    - {item}" for item in assessment[key])
                    swot_parts.append(f"  **{key.title()}**:\n{items}")
            if swot_parts:
                description_parts.append(f"**SWOT Analysis**:\n" + '\n'.join(swot_parts))
        
        # Add categories
        if 'categories' in analysis and analysis['categories']:
            categories = ', '.join(analysis['categories'])
            description_parts.append(f"**Categories**: {categories}")
        
        return '\n\n'.join(description_parts)


async def main():
    """Test function for LLM analyzer."""
    analyzer = LLMAnalyzer()
    
    # Test HTML content
    test_html = """
    <div>
        <h2>Inspiration</h2>
        <p>The economy is in crisis mode currently. We decided we need to know how we can better understand and predict where stocks are going to move in the future.</p>
        
        <h2>What it does</h2>
        <p>MTG Advisor is your AI Parent that helps you analyze the most recently filed insider trades made by US senators.</p>
        
        <h2>How we built it</h2>
        <p>MTG Advisor is built almost entirely out of React and Flask.</p>
    </div>
    """
    
    analysis = await analyzer.analyze_project_content(test_html, "MTG Advisor")
    print("Analysis:", analysis)
    
    description = analyzer.create_enhanced_description(analysis)
    print("Enhanced Description:", description)


if __name__ == "__main__":
    import asyncio
    import sys
    sys.path.append("..")
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())