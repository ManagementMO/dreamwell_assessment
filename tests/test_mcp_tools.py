"""
Dreamwell Agent - MCP Tool Unit Tests

Tests individual MCP tools in isolation
"""

import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestEmailTools:
    """Test email-related MCP tools"""
    
    def test_get_email_thread_exists(self):
        """Test fetching existing email thread"""
        from mcp_server import get_email_thread
        
        result = get_email_thread("thread_001")
        
        assert result["success"] == True
        assert "data" in result
        assert result["data"]["thread_id"] == "thread_001"
        assert result["data"]["category"] == "price_negotiation"
    
    def test_get_email_thread_not_found(self):
        """Test fetching non-existent thread"""
        from mcp_server import get_email_thread
        
        result = get_email_thread("nonexistent_thread")
        
        assert result["success"] == False
        assert "error" in result
    
    def test_get_latest_emails_default(self):
        """Test listing emails with default limit"""
        from mcp_server import get_latest_emails
        
        result = get_latest_emails()
        
        assert result["success"] == True
        assert len(result["data"]) <= 10  # Default limit
    
    def test_get_latest_emails_custom_limit(self):
        """Test listing emails with custom limit"""
        from mcp_server import get_latest_emails
        
        result = get_latest_emails(limit=5)
        
        assert result["success"] == True
        assert len(result["data"]) <= 5


class TestBrandTools:
    """Test brand-related MCP tools"""
    
    def test_get_brand_context_perplexity(self):
        """Test fetching Perplexity brand context"""
        from mcp_server import get_brand_context
        
        result = get_brand_context("perplexity")
        
        assert result["success"] == True
        assert "data" in result
        assert result["data"]["brand_id"] == "perplexity"
    
    def test_get_brand_context_not_found(self):
        """Test fetching non-existent brand"""
        from mcp_server import get_brand_context
        
        result = get_brand_context("nonexistent_brand")
        
        assert result["success"] == False


class TestYouTubeTools:
    """Test YouTube data tools with fallback"""
    
    def test_fetch_channel_data_fallback(self):
        """Test fetching channel data (uses fallback)"""
        from mcp_server import fetch_channel_data
        
        result = fetch_channel_data("https://www.youtube.com/@TechReviewAlex")
        
        assert result["success"] == True
        assert "data" in result
        assert result["data"]["subscribers"] > 0
    
    def test_fetch_channel_data_not_found(self):
        """Test fetching non-existent channel"""
        from mcp_server import fetch_channel_data
        
        result = fetch_channel_data("https://www.youtube.com/@NonexistentChannel12345")
        
        # Without API key, this should fail as it won't be in local data
        assert result["success"] == False
    
    def test_calculate_engagement(self):
        """Test engagement calculation"""
        from mcp_server import calculate_engagement
        
        result = calculate_engagement("UCtech_alex")
        
        assert result["success"] == True
        assert "engagement_rate" in result


class TestPricingTools:
    """Test pricing calculation tools"""
    
    def test_calculate_offer_price(self):
        """Test offer price calculation"""
        from mcp_server import calculate_offer_price
        
        result = calculate_offer_price(
            "https://www.youtube.com/@TechReviewAlex",
            "integration",
            "perplexity"
        )
        
        assert result["success"] == True
        assert "calculation" in result
        
        calc = result["calculation"]
        assert "final_cpm" in calc
        assert "estimated_total_price" in calc
        assert calc["estimated_total_price"] > 0
    
    def test_validate_counter_offer_accept(self):
        """Test counter-offer validation (should accept)"""
        from mcp_server import validate_counter_offer
        
        result = validate_counter_offer(
            "https://www.youtube.com/@TechReviewAlex",
            1000.0,  # Original
            1050.0   # Counter (+5%)
        )
        
        assert result["success"] == True
        assert result["analysis"]["recommendation"] == "accept"
    
    def test_validate_counter_offer_negotiate(self):
        """Test counter-offer validation (should negotiate)"""
        from mcp_server import validate_counter_offer
        
        result = validate_counter_offer(
            "https://www.youtube.com/@TechReviewAlex",
            1000.0,  # Original
            1200.0   # Counter (+20%)
        )
        
        assert result["success"] == True
        assert result["analysis"]["recommendation"] == "negotiate"
    
    def test_validate_counter_offer_decline(self):
        """Test counter-offer validation (should decline)"""
        from mcp_server import validate_counter_offer
        
        result = validate_counter_offer(
            "https://www.youtube.com/@TechReviewAlex",
            1000.0,  # Original
            1600.0   # Counter (+60%)
        )
        
        assert result["success"] == True
        assert result["analysis"]["recommendation"] == "decline"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
