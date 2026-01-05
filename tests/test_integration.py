"""
Dreamwell Agent - Integration Tests

Tests the full stack: MCP Server → Backend API → Agent Orchestrator
"""

import pytest
import asyncio
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMCPTools:
    """Test MCP server tools directly"""
    
    @pytest.fixture
    def email_fixtures(self):
        """Load email fixtures"""
        with open('data/email_fixtures.json', 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def youtube_profiles(self):
        """Load YouTube profiles"""
        with open('data/youtube_profiles.json', 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def brand_profiles(self):
        """Load brand profiles"""
        with open('data/brand_profiles.json', 'r') as f:
            return json.load(f)
    
    def test_email_fixtures_count(self, email_fixtures):
        """Verify we have 20+ email scenarios"""
        assert len(email_fixtures) >= 20, f"Expected 20+ emails, got {len(email_fixtures)}"
    
    def test_email_categories_distribution(self, email_fixtures):
        """Verify email category distribution"""
        categories = {}
        for email in email_fixtures:
            cat = email.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        # Required categories
        assert 'not_interested' in categories, "Missing not_interested category"
        assert 'price_negotiation' in categories, "Missing price_negotiation category"
        assert 'acceptance' in categories, "Missing acceptance category"
        assert 'bulk_deal' in categories, "Missing bulk_deal category"
        assert 'clarification' in categories, "Missing clarification category"
        
        # Count checks
        assert categories.get('not_interested', 0) >= 5, "Need at least 5 not_interested"
        assert categories.get('price_negotiation', 0) >= 6, "Need at least 6 price_negotiation"
        assert categories.get('acceptance', 0) >= 3, "Need at least 3 acceptance"
        assert categories.get('bulk_deal', 0) >= 4, "Need at least 4 bulk_deal"
        assert categories.get('clarification', 0) >= 2, "Need at least 2 clarification"
    
    def test_youtube_profiles_count(self, youtube_profiles):
        """Verify we have 10+ YouTube profiles"""
        assert len(youtube_profiles) >= 10, f"Expected 10+ profiles, got {len(youtube_profiles)}"
    
    def test_youtube_profiles_have_required_fields(self, youtube_profiles):
        """Verify YouTube profiles have all required fields"""
        required_fields = [
            'channel_id', 'channel_url', 'channel_name', 'subscribers',
            'avg_views_per_video', 'engagement_rate', 'category', 'consistency_score'
        ]
        
        for profile in youtube_profiles:
            for field in required_fields:
                assert field in profile, f"Profile {profile.get('channel_name')} missing {field}"
    
    def test_brand_profiles_exist(self, brand_profiles):
        """Verify brand profiles exist"""
        assert len(brand_profiles) >= 2, "Need at least 2 brand profiles"
        
        brand_ids = [b.get('brand_id') for b in brand_profiles]
        assert 'perplexity' in brand_ids, "Missing perplexity brand"


class TestPricingLogic:
    """Test CPM pricing calculations"""
    
    def test_base_cpm_tiers(self):
        """Test base CPM tier assignment"""
        from mcp_server import get_base_cpm
        
        assert get_base_cpm(5000) == 12.50, "Micro tier should be $12.50"
        assert get_base_cpm(50000) == 20.00, "Mid tier should be $20.00"
        assert get_base_cpm(300000) == 32.50, "Macro tier should be $32.50"
        assert get_base_cpm(2000000) == 70.00, "Mega tier should be $70.00"
    
    def test_engagement_multiplier(self):
        """Test engagement multiplier calculation"""
        from mcp_server import get_engagement_multiplier
        
        assert get_engagement_multiplier(0.03) == 0.7, "Low engagement = 0.7x"
        assert get_engagement_multiplier(0.10) == 1.0, "Average engagement = 1.0x"
        assert get_engagement_multiplier(0.20) == 1.3, "High engagement = 1.3x"
        assert get_engagement_multiplier(0.35) == 1.5, "Viral engagement = 1.5x"
    
    def test_niche_multiplier(self):
        """Test niche multiplier detection"""
        from mcp_server import get_niche_multiplier
        
        assert get_niche_multiplier("Tech Reviews", "AI and technology") == 1.2
        assert get_niche_multiplier("Finance Tips", "Personal finance and money") == 1.4
        assert get_niche_multiplier("Gaming Channel", "Let's plays and gaming") == 0.9
        assert get_niche_multiplier("Lifestyle", "Daily vlogs") == 1.0
    
    def test_consistency_multiplier(self):
        """Test consistency score multiplier"""
        from mcp_server import get_consistency_multiplier
        
        assert get_consistency_multiplier("high") == 1.1
        assert get_consistency_multiplier("medium") == 1.0
        assert get_consistency_multiplier("low") == 0.9


class TestAPIEndpoints:
    """Test FastAPI endpoints (requires running server)"""
    
    @pytest.fixture
    def base_url(self):
        return "http://localhost:8000/api"
    
    @pytest.mark.asyncio
    async def test_list_emails_endpoint(self, base_url):
        """Test GET /emails endpoint"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/emails?limit=10") as resp:
                assert resp.status == 200
                data = await resp.json()
                assert data.get("success") == True
                assert "data" in data
                assert len(data["data"]) <= 10
    
    @pytest.mark.asyncio
    async def test_get_thread_endpoint(self, base_url):
        """Test GET /emails/{thread_id} endpoint"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/emails/thread_001") as resp:
                assert resp.status == 200
                data = await resp.json()
                assert data.get("success") == True
                thread = data.get("data", {})
                assert thread.get("thread_id") == "thread_001"
                assert "thread" in thread
    
    @pytest.mark.asyncio
    async def test_get_thread_not_found(self, base_url):
        """Test 404 for non-existent thread"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/emails/nonexistent_thread") as resp:
                data = await resp.json()
                # Should return success: false, not 404
                assert data.get("success") == False


class TestAgentOrchestrator:
    """Test the ReAct loop agent (requires OpenAI API key)"""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="No OpenAI API key")
    async def test_generate_response_endpoint(self):
        """Test POST /generate endpoint"""
        import aiohttp
        
        base_url = "http://localhost:8000/api"
        payload = {
            "thread_id": "thread_001",
            "brand_id": "perplexity"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/generate", 
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                assert resp.status == 200
                data = await resp.json()
                
                # Should have response draft
                assert "response_draft" in data
                assert len(data["response_draft"]) > 0
                
                # Should have pricing breakdown
                assert "pricing_breakdown" in data
                
                # Should track iterations
                assert "iterations_used" in data
                assert data["iterations_used"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
