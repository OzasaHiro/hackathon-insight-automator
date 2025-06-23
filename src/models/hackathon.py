"""
Data models for hackathon data.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class ProjectMember(BaseModel):
    """Represents a project team member."""
    name: str
    profile_url: Optional[HttpUrl] = None
    role: Optional[str] = None


class Award(BaseModel):
    """Represents an award/prize won by a project."""
    name: str
    category: Optional[str] = None
    sponsor: Optional[str] = None
    prize_value: Optional[str] = None


class Project(BaseModel):
    """Represents a hackathon project."""
    name: str
    description: str
    devpost_url: HttpUrl
    project_url: Optional[HttpUrl] = None
    tags: List[str] = Field(default_factory=list)
    awards: List[Award] = Field(default_factory=list)
    members: List[ProjectMember] = Field(default_factory=list)
    submission_date: Optional[datetime] = None
    image_url: Optional[HttpUrl] = None
    vote_count: Optional[int] = None
    comment_count: Optional[int] = None
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Hackathon(BaseModel):
    """Represents a hackathon event."""
    name: str
    description: Optional[str] = None
    devpost_url: HttpUrl
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    theme: Optional[str] = None
    prizes: List[str] = Field(default_factory=list)
    sponsors: List[str] = Field(default_factory=list)
    participant_count: Optional[int] = None
    submission_count: Optional[int] = None
    projects: List[Project] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ScrapingResult(BaseModel):
    """Represents the result of a scraping operation."""
    success: bool
    url: HttpUrl
    hackathon: Optional[Hackathon] = None
    error_message: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }