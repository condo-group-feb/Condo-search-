"""Custom exceptions for scraper module."""


class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass


class LoginError(ScraperError):
    """Exception raised when login fails."""
    pass


class NavigationError(ScraperError):
    """Exception raised when navigation fails."""
    pass


class ElementNotFoundError(ScraperError):
    """Exception raised when an element cannot be found."""
    pass


class SessionError(ScraperError):
    """Exception raised for session-related errors."""
    pass











