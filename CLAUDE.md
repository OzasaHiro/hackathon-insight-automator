# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Hackathon Insight Automator** (仮) project - currently in the specification phase. The project aims to automate the collection and analysis of hackathon data to identify winning trends and generate MVP ideas.

## Current State

**Pre-implementation phase** - Only specification document exists (`Spec.md` in Japanese).

## Execution Model

This application is designed to run as a **standalone Python application** for personal use. When executed, it will:
1. Collect hackathon data
2. Analyze winning projects
3. Generate reports locally

Future plans include deployment for scheduled execution and automated reporting, but the initial implementation focuses on local execution.

## Planned Architecture

### Technology Stack
- **Frontend**: Next.js + Tailwind CSS (for future dashboard)
- **Backend**: Python (FastAPI), Playwright, LangChain
- **Database**: Supabase (PostgreSQL with Row-Level Security)
- **AI/ML**: OpenAI o3 / OpenLLM + LangChain
- **Future CI/CD**: GitHub Actions (for scheduled runs when deployed)

### Core Components
1. **Data Collection**: Playwright-based web scraping for Devpost
2. **Storage**: PostgreSQL via Supabase
3. **Analysis**: LangChain pipeline for LLM processing
4. **Distribution**: Markdown reports (local), future: Next.js dashboard

## Development Guidelines

When implementing this project:

### Backend (Python/FastAPI)
- Use FastAPI for API endpoints
- Implement Playwright scrapers with proper error handling and rate limiting
- Structure LangChain pipelines in modular, testable components
- Follow PEP 8 style guidelines

### Frontend (Next.js)
- Use App Router for Next.js 14+
- Implement Tailwind CSS for styling
- Create reusable components in `components/` directory
- Use TypeScript for type safety

### Database
- Design schema with Row-Level Security in mind
- Create proper indexes for query performance
- Use Supabase client libraries for interactions

## Key Features to Implement

1. **On-Demand Data Collection**: Execute Python script to scrape hackathon platforms
2. **LLM Analysis**: Process winning projects to extract trends
3. **Report Generation**: Create markdown reports saved locally
4. **Trend Visualization**: 4-week moving average charts (in reports)
5. **Compliance Management**: Respect robots.txt and implement rate limiting

## Important Considerations

- The specification is in Japanese - refer to `Spec.md` for detailed requirements
- Implement proper error handling for web scraping failures
- Ensure compliance with website terms of service
- Design for scalability as data volume grows
- Implement comprehensive logging for debugging