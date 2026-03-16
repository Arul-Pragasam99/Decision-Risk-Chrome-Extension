"""API call utilities for fetching price data from external services.

This module provides functions to fetch price data from various sources.
In production, this would connect to real APIs with proper authentication.
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import hashlib
import time
from typing import Dict, Any, Optional, List
from datetime import datetime


class ApiClient:
    """Base API client with rate limiting and error handling."""
    
    def __init__(self, rate_limit: int = 10, rate_period: int = 60):
        """Initialize API client.
        
        Args:
            rate_limit: Maximum number of requests per rate_period
            rate_period: Period in seconds for rate limiting
        """
        self.rate_limit = rate_limit
        self.rate_period = rate_period
        self.request_timestamps = []
    
    def _check_rate_limit(self):
        """Check if rate limit is exceeded."""
        now = time.time()
        # Remove timestamps older than rate_period
        self.request_timestamps = [t for t in self.request_timestamps 
                                   if now - t < self.rate_period]
        
        if len(self.request_timestamps) >= self.rate_limit:
            wait_time = self.rate_period - (now - self.request_timestamps[0])
            if wait_time > 0:
                time.sleep(wait_time)
        
        self.request_timestamps.append(now)
    
    def fetch_json(self, url: str, params: Optional[Dict] = None, 
                   headers: Optional[Dict] = None, timeout: int = 10) -> Dict:
        """Fetch JSON from a URL with rate limiting."""
        self._check_rate_limit()
        
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        
        request = urllib.request.Request(url)
        if headers:
            for key, value in headers.items():
                request.add_header(key, value)
        
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                content = response.read().decode('utf-8')
                return json.loads(content)
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
            print(f"API request failed: {e}")
            return {}


class PriceApiClient(ApiClient):
    """Client for fetching price data from various sources."""
    
    def __init__(self):
        super().__init__(rate_limit=30, rate_period=60)
        # Mock API endpoints - in production, use real APIs
        self.apis = {
            'amazon': 'https://api.example.com/amazon/price',
            'flipkart': 'https://api.example.com/flipkart/price',
            'camelcamelcamel': 'https://api.example.com/ccc/history',
            'keepa': 'https://api.example.com/keepa/product'
        }
    
    def fetch_current_price(self, platform: str, product_id: str) -> Optional[float]:
        """Fetch current price from platform."""
        # This is a mock implementation
        # In production, this would call actual APIs
        
        # Simulate API call
        mock_prices = {
            'amazon': 19999,
            'flipkart': 19499,
            'myntra': 2499,
            'ajio': 2299
        }
        
        return mock_prices.get(platform)
    
    def fetch_price_history(self, platform: str, product_id: str, 
                           days: int = 90) -> List[Dict]:
        """Fetch historical price data."""
        # Mock historical data
        import random
        
        history = []
        base_price = random.randint(10000, 50000)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        while current_date <= end_date:
            # Add some randomness
            price = base_price * (1 + random.uniform(-0.15, 0.15))
            
            history.append({
                'timestamp': current_date.timestamp(),
                'date': current_date.isoformat(),
                'price': round(price, 2)
            })
            
            current_date += timedelta(days=1)
        
        return history
    
    def search_alternatives(self, product_title: str, 
                           max_results: int = 5) -> List[Dict]:
        """Search for alternative products across platforms."""
        # Mock alternative search
        alternatives = []
        platforms = ['Amazon India', 'Flipkart', 'Myntra', 'AJIO', 'Tata CLiQ']
        
        import random
        base_price = random.randint(1000, 50000)
        
        for i, platform in enumerate(platforms[:max_results]):
            # Random price variation
            price = base_price * random.uniform(0.8, 1.2)
            
            alternatives.append({
                'platform': platform,
                'title': f"{product_title} - {platform}",
                'price': round(price, 2),
                'url': f"https://www.{platform.lower().replace(' ', '')}.com/search",
                'confidence': random.uniform(0.7, 0.95)
            })
        
        # Sort by price
        alternatives.sort(key=lambda x: x['price'])
        
        return alternatives


class PriceComparisonClient(ApiClient):
    """Client for comparing prices across platforms."""
    
    def __init__(self):
        super().__init__(rate_limit=20, rate_period=60)
    
    def compare_prices(self, product_title: str) -> Dict[str, Any]:
        """Compare prices across multiple platforms."""
        # Mock comparison data
        platforms = {
            'Amazon India': {'price': None, 'url': None, 'in_stock': True},
            'Flipkart': {'price': None, 'url': None, 'in_stock': True},
            'Myntra': {'price': None, 'url': None, 'in_stock': True},
            'AJIO': {'price': None, 'url': None, 'in_stock': True},
            'Tata CLiQ': {'price': None, 'url': None, 'in_stock': True},
            'Snapdeal': {'price': None, 'url': None, 'in_stock': True}
        }
        
        import random
        base_price = random.randint(1000, 50000)
        
        for platform in platforms:
            # Random price variation
            price = base_price * random.uniform(0.85, 1.25)
            platforms[platform]['price'] = round(price, 2)
            platforms[platform]['url'] = f"https://www.{platform.lower().replace(' ', '')}.com/search"
        
        # Find best price
        best_platform = min(platforms.items(), key=lambda x: x[1]['price'])
        
        return {
            'product': product_title,
            'platforms': platforms,
            'best_price': {
                'platform': best_platform[0],
                'price': best_platform[1]['price'],
                'url': best_platform[1]['url']
            },
            'price_range': {
                'min': min(p['price'] for p in platforms.values()),
                'max': max(p['price'] for p in platforms.values())
            },
            'savings_potential': self._calculate_savings(platforms)
        }
    
    def _calculate_savings(self, platforms: Dict) -> Dict:
        """Calculate potential savings by choosing best platform."""
        prices = [p['price'] for p in platforms.values()]
        if not prices:
            return {'amount': 0, 'percentage': 0}
        
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        
        return {
            'amount': round(avg_price - min_price, 2),
            'percentage': round((avg_price - min_price) / avg_price * 100, 1)
        }


# Create global instances
price_client = PriceApiClient()
comparison_client = PriceComparisonClient()


# Convenience functions
def fetch_price_history_from_api(product_url: str) -> Dict:
    """Fetch price history from API (mock implementation)."""
    # Extract product ID from URL (simplified)
    import re
    
    # Try to extract ASIN from Amazon URL
    asin_match = re.search(r'/dp/([A-Z0-9]{10})', product_url)
    if asin_match:
        product_id = asin_match.group(1)
        platform = 'amazon'
    else:
        # Fallback
        product_id = hashlib.md5(product_url.encode()).hexdigest()[:10]
        platform = 'unknown'
    
    history = price_client.fetch_price_history(platform, product_id)
    
    return {
        'product_id': product_id,
        'platform': platform,
        'history': history,
        'current_price': history[-1]['price'] if history else None,
        'history_length': len(history)
    }


def search_alternative_sellers(product_title: str) -> List[Dict]:
    """Search for alternative sellers."""
    return price_client.search_alternatives(product_title)


def get_price_comparison(product_title: str) -> Dict:
    """Get price comparison across platforms."""
    return comparison_client.compare_prices(product_title)


# Add missing import at the top
from datetime import timedelta