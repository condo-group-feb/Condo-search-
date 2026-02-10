"""Pydantic schemas for API requests and responses."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Request model for login."""
    username: str = Field(..., description="MLS Username")
    password: str = Field(..., description="Password")


class SearchFiltersRequest(BaseModel):
    """Request model for search filters."""
    street_number: str = Field(..., description="Street number (e.g., '30', '90')")
    street_direction: str = Field(..., description="Street direction: N, NE, E, SE, S, SW, W, NW")
    street_name: str = Field(..., description="Street name (e.g., '3', '3rd')")


class ScrapeResponse(BaseModel):
    """Response model for scrape endpoint."""
    status: str = Field(..., description="Status of the operation")
    message: str = Field(..., description="Status message")
    current_url: str = Field(None, description="Current URL after navigation")
    success: bool = Field(..., description="Whether the operation was successful")
    data: dict = Field(default_factory=dict, description="Extracted mortgage history data with ML# as keys")



