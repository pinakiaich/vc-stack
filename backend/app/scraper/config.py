"""
Scraper Configuration
Filter criteria and settings for company research agent
"""

# Company filter criteria
COMPANY_FILTERS = {
    "stage": ["Series B", "Series C"],
    "valuation_min": 100_000_000,  # $100M
    "valuation_max": 500_000_000,  # $500M
    "location": ["United States", "US", "USA"],
    "exclude_industries": ["Crypto", "Cannabis"],
}

# Scraper settings
SCRAPER_SETTINGS = {
    "rate_limit_delay": 1.0,  # Seconds between requests
    "max_retries": 3,
    "timeout_seconds": 30,
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}

# Data source priorities (higher = more reliable)
SOURCE_PRIORITY = {
    "yc": 0.9,
    "techcrunch": 0.7,
    "newsapi": 0.6,
    "open_data": 0.5,
}
