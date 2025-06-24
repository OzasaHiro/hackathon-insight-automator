# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Hackathon Insight Automator** project - a fully implemented Python application that automates the collection and analysis of hackathon data to identify winning trends and generate MVP ideas.

## Repository Management

This project is managed on GitHub:
- **Repository**: https://github.com/OzasaHiro/hackathon-insight-automator
- **Visibility**: Public repository
- **Branch**: main
- **Version Control**: All development tracked with comprehensive commit history

## Current State

**Production-ready** - Complete implementation with all core features working:
- ✅ AI hackathon search and selection
- ✅ Google Gemini 2.5 Flash LLM integration
- ✅ Web scraping with Playwright
- ✅ Markdown report generation
- ✅ Rich CLI interface

## Execution Model

This application is designed to run as a **standalone Python application** for personal use. When executed, it will:
1. Collect hackathon data
2. Analyze winning projects
3. Generate reports locally

Future plans include deployment for scheduled execution and automated reporting, but the initial implementation focuses on local execution.

## Implemented Architecture

### Technology Stack
- **Backend**: Python with Playwright, Pydantic, Rich CLI
- **AI/ML**: Google Generative AI (Gemini 2.5 Flash)
- **Web Scraping**: Playwright with multi-browser fallback (Chromium/Firefox/WebKit)
- **Reports**: Jinja2 templates for Markdown generation
- **CLI**: Rich library for beautiful terminal interface

### Core Components
1. **Data Collection**: ✅ Playwright-based web scraping for Devpost
2. **Storage**: ✅ JSON file storage with structured data models
3. **Analysis**: ✅ Google Gemini pipeline for LLM processing
4. **Distribution**: ✅ Markdown reports (local)

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

## Implemented Key Features

1. **✅ On-Demand Data Collection**: Execute Python script to scrape hackathon platforms
2. **✅ AI Hackathon Search**: Automatic discovery of recent AI hackathons from Devpost
3. **✅ LLM Analysis**: Process winning projects to extract trends using Gemini 2.5 Flash
4. **✅ Report Generation**: Create comprehensive markdown reports saved locally
5. **✅ Interactive CLI**: Rich terminal interface with progress indicators and selection menus
6. **✅ Multi-browser Support**: Chromium/Firefox/WebKit fallback for reliability
7. **✅ Compliance Management**: Respect rate limiting and implement proper delays

## Important Considerations

- The specification is in Japanese - refer to `Spec.md` for detailed requirements
- Implement proper error handling for web scraping failures
- Ensure compliance with website terms of service
- Design for scalability as data volume grows
- Implement comprehensive logging for debugging