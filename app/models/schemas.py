"""Pydantic schemas for API requests and responses."""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Request model for login."""
    username: str = Field(..., description="MLS Username")
    password: str = Field(..., description="Password")


class SearchFiltersRequest(BaseModel):
    """Request model for search filters."""
    street_number: str = Field(..., description="Street number (e.g., '30', '90')")
    street_direction: Optional[str] = Field(None, description="Street direction: N, NE, E, SE, S, SW, W, NW (optional)")
    street_name: str = Field(..., description="Street name (e.g., '3', '3rd')")
    webhook_url: Optional[str] = Field(None, description="URL to POST results back to (optional, will use WEBHOOK_URL from .env if not provided)")
    search_id: Optional[str] = Field(None, description="Search ID from database (if provided, will be used instead of generating new one)")


class ScrapeResponse(BaseModel):
    """Response model for scrape endpoint."""
    status: str = Field(..., description="Status of the operation")
    message: str = Field(..., description="Status message")
    current_url: Optional[str] = Field(None, description="Current URL after navigation")
    success: bool = Field(..., description="Whether the operation was successful")
    data: dict = Field(default_factory=dict, description="Extracted mortgage history data with ML# as keys")
    search_id: str = Field(..., description="Unique UUID generated for this search")



