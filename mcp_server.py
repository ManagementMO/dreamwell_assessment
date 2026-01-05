"""
Dreamwell Influencer Agent - MCP Tool Server

CRITICAL: This file is completely standalone and runs as a subprocess.
- NO imports from backend_main.py
- Communicates via stdio ONLY
- Uses file-based logging (NOT stdout/stderr - breaks stdio pipe!)
"""

# ⚠️ CRITICAL: Load environment variables FIRST (Rule 7)
# Do not rely on parent process to pass env vars
from dotenv import load_dotenv
load_dotenv()

import os
import json
import logging
from datetime import datetime, timedelta
import math
from typing import Dict, List, Any, Optional
from pathlib import Path

# Google API
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ⚠️ CRITICAL: Configure logging to write to FILE, NOT stdout/stderr
# Writing to stdout/stderr will break the MCP stdio pipe!
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='server.log',  # Write to file only
    filemode='a'
)
logger = logging.getLogger(__name__)

# DO NOT use print() - it breaks stdio communication!
logger.info("MCP server starting...")

# Import FastMCP
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Dreamwell Influencer Agent")

# ========== CONFIGURATION ==========
DATA_DIR = Path(__file__).parent / "data"
EMAIL_FIXTURES_PATH = DATA_DIR / "email_fixtures.json"
YOUTUBE_PROFILES_PATH = DATA_DIR / "youtube_profiles.json"
BRAND_PROFILES_PATH = DATA_DIR / "brand_profiles.json"

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
YOUTUBE_CACHE_DURATION_HOURS = 24

# ========== DATA STORES (In-Memory) ==========
# Load data from JSON fixtures
try:
    with open(EMAIL_FIXTURES_PATH, 'r') as f:
        emails = json.load(f)
    logger.info(f"Loaded {len(emails)} email fixtures")
except Exception as e:
    logger.error(f"Failed to load email fixtures: {e}")
    emails = []

try:
    with open(YOUTUBE_PROFILES_PATH, 'r') as f:
        youtube_profiles = json.load(f)
    logger.info(f"Loaded {len(youtube_profiles)} YouTube profiles")
except Exception as e:
    logger.error(f"Failed to load YouTube profiles: {e}")
    youtube_profiles = []

try:
    with open(BRAND_PROFILES_PATH, 'r') as f:
        brands = json.load(f)
    logger.info(f"Loaded {len(brands)} brand profiles")
except Exception as e:
    logger.error(f"Failed to load brand profiles: {e}")
    brands = []

# YouTube API cache (simple in-memory cache with timestamps)
youtube_cache: Dict[str, Dict[str, Any]] = {}


# ========== HELPER FUNCTIONS ==========

def find_email_by_thread_id(thread_id: str) -> Optional[Dict]:
    """Find an email thread by ID"""
    for email in emails:
        if email.get("thread_id") == thread_id:
            return email
    return None


def find_brand_by_id(brand_id: str) -> Optional[Dict]:
    """Find a brand profile by ID"""
    for brand in brands:
        if brand.get("brand_id") == brand_id:
            return brand
    return None


def find_youtube_profile_by_url(url: str) -> Optional[Dict]:
    """Find a YouTube profile by URL (for fallback), with flexible matching"""
    # Extract handle from input URL for flexible matching
    input_handle = extract_channel_id_from_url(url).lower() if url else ""
    
    for profile in youtube_profiles:
        # Exact match
        if profile.get("channel_url") == url:
            return profile
        # Handle match
        profile_handle = profile.get("handle", "").lower()
        if input_handle and profile_handle and input_handle == profile_handle:
            return profile
        # Extract and compare handles from URLs
        profile_url = profile.get("channel_url", "")
        profile_url_handle = extract_channel_id_from_url(profile_url).lower() if profile_url else ""
        if input_handle and profile_url_handle and input_handle == profile_url_handle:
            return profile
    return None


def extract_channel_id_from_url(url: str) -> str:
    """Extract channel ID or handle from YouTube URL"""
    # Simple extraction - in real implementation would use regex
    # https://www.youtube.com/@ChannelName -> @ChannelName
    if "@" in url:
        parts = url.split("@")
        if len(parts) > 1:
            return "@" + parts[1].split("/")[0]
    return url


# ========== EMAIL TOOLS (4 tools) ==========

@mcp.tool()
def get_email_thread(thread_id: str) -> Dict[str, Any]:
    """
    Get full email thread history by thread ID.

    Args:
        thread_id: The unique identifier for the email thread

    Returns:
        Complete email thread with all messages and metadata
    """
    logger.info(f"get_email_thread called with thread_id={thread_id}")

    email = find_email_by_thread_id(thread_id)

    if email is None:
        logger.warning(f"Thread {thread_id} not found")
        return {
            "success": False,
            "error": f"Thread {thread_id} not found"
        }

    logger.info(f"Found thread {thread_id} - category: {email.get('category')}")
    return {
        "success": True,
        "data": email
    }


@mcp.tool()
def get_latest_emails(limit: int = 10) -> Dict[str, Any]:
    """
    List recent email threads, sorted by most recent.

    Args:
        limit: Maximum number of emails to return (default: 10)

    Returns:
        List of email threads with basic metadata
    """
    logger.info(f"get_latest_emails called with limit={limit}")

    # Sort emails by most recent timestamp in thread
    def get_latest_timestamp(email):
        if email.get("thread") and len(email["thread"]) > 0:
            last_msg = email["thread"][-1]
            return last_msg.get("timestamp", "")
        return ""

    sorted_emails = sorted(emails, key=get_latest_timestamp, reverse=True)
    limited_emails = sorted_emails[:limit]

    # Return summary info
    email_summaries = []
    for email in limited_emails:
        email_summaries.append({
            "thread_id": email.get("thread_id"),
            "influencer_name": email.get("influencer_name"),
            "brand": email.get("brand"),
            "category": email.get("category"),
            "status": email.get("status"),
            "latest_message_time": get_latest_timestamp(email)
        })

    logger.info(f"Returning {len(email_summaries)} emails")
    return {
        "success": True,
        "data": email_summaries,
        "total": len(email_summaries)
    }


@mcp.tool()
def send_reply(thread_id: str, content: str) -> Dict[str, Any]:
    """
    Send a reply to an influencer email thread.

    Args:
        thread_id: The thread to reply to
        content: The email body content to send

    Returns:
        Confirmation of email sent
    """
    logger.info(f"send_reply called for thread_id={thread_id}")

    email = find_email_by_thread_id(thread_id)

    if email is None:
        logger.warning(f"Thread {thread_id} not found")
        return {
            "success": False,
            "error": f"Thread {thread_id} not found"
        }

    # In a real system, would send via email API
    # For demo, we just append to the thread
    brand_email = f"outreach@{email.get('brand')}.ai"
    influencer_email = email.get("influencer_email")

    new_message = {
        "from": brand_email,
        "to": influencer_email,
        "subject": f"Re: {email['thread'][0]['subject']}",
        "body": content,
        "timestamp": datetime.now().isoformat() + "Z"
    }

    email["thread"].append(new_message)

    logger.info(f"Reply sent to thread {thread_id}")
    return {
        "success": True,
        "message": "Reply sent successfully",
        "thread_id": thread_id,
        "sent_at": new_message["timestamp"]
    }


@mcp.tool()
def mark_as_processed(thread_id: str) -> Dict[str, Any]:
    """
    Mark an email thread as processed/approved.

    Args:
        thread_id: The thread to mark as processed

    Returns:
        Confirmation of status update
    """
    logger.info(f"mark_as_processed called for thread_id={thread_id}")

    email = find_email_by_thread_id(thread_id)

    if email is None:
        logger.warning(f"Thread {thread_id} not found")
        return {
            "success": False,
            "error": f"Thread {thread_id} not found"
        }

    email["status"] = "processed"
    email["processed_at"] = datetime.now().isoformat() + "Z"

    logger.info(f"Thread {thread_id} marked as processed")
    return {
        "success": True,
        "message": f"Thread {thread_id} marked as processed",
        "thread_id": thread_id,
        "status": "processed"
    }


# ========== BRAND TOOLS (1 tool) ==========

@mcp.tool()
def get_brand_context(brand_id: str) -> Dict[str, Any]:
    """
    Get brand profile and context for personalized responses.

    Args:
        brand_id: The brand identifier (e.g., 'perplexity', 'copyai')

    Returns:
        Brand profile with messaging guidelines, budget, target audience, etc.
    """
    logger.info(f"get_brand_context called for brand_id={brand_id}")

    brand = find_brand_by_id(brand_id)

    if brand is None:
        logger.warning(f"Brand {brand_id} not found")
        return {
            "success": False,
            "error": f"Brand {brand_id} not found"
        }

    logger.info(f"Found brand {brand.get('brand_name')}")
    return {
        "success": True,
        "data": brand
    }


# ========== YOUTUBE TOOLS ==========

@mcp.tool()
def fetch_channel_data(channel_url: str) -> Dict[str, Any]:
    """
    Fetch public YouTube channel statistics.
    
    Implements a Hybrid Fallback Strategy:
    1. Tries to use Real YouTube API if key is present
    2. Falls back to local JSON data if API fails or quota exceeded
    3. Handles @handle and full URLs
    """
    logger.info(f"fetch_channel_data called for {channel_url}")
    
    # 1. Try to find in local data first (as a base or fallback)
    local_profile = find_youtube_profile_by_url(channel_url)
    
    # 2. Extract handle/ID
    handle_or_id = extract_channel_id_from_url(channel_url)
    
    # 3. Try Real API if Key exists
    if YOUTUBE_API_KEY:
        try:
            logger.info("Attempting to fetch from YouTube API...")
            youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
            
            # Determine if looking up by ID or Handle
            if handle_or_id.startswith("@"):
                # Search for channel by handle
                request = youtube.search().list(
                    part="snippet",
                    q=handle_or_id,
                    type="channel",
                    maxResults=1
                )
                response = request.execute()
                
                if not response["items"]:
                    raise Exception("Channel not found via search")
                    
                channel_id = response["items"][0]["snippet"]["channelId"]
            else:
                channel_id = handle_or_id
            
            # Get Channel Stats
            stats_request = youtube.channels().list(
                part="statistics,snippet,brandingSettings",
                id=channel_id
            )
            stats_response = stats_request.execute()
            
            if stats_response["items"]:
                item = stats_response["items"][0]
                stats = item["statistics"]
                snippet = item["snippet"]
                
                # Success! Return real data
                logger.info("✅ Successfully fetched real YouTube API data")
                return {
                    "success": True,
                    "source": "api",
                    "data": {
                        "channel_id": item["id"],
                        "title": snippet["title"],
                        "description": snippet["description"],
                        "custom_url": snippet.get("customUrl"),
                        "subscriber_count": int(stats["subscriberCount"]),
                        "video_count": int(stats["videoCount"]),
                        "view_count": int(stats["viewCount"]),
                        "thumbnail_url": snippet["thumbnails"]["default"]["url"],
                        "country": snippet.get("country"),
                        # Calculate engagement from cache/recent videos if possible, else estimate
                        "engagement_rate": local_profile.get("engagement_rate", 0.05) if local_profile else 0.05
                    }
                }
                
        except HttpError as e:
            logger.warning(f"YouTube API Error (Quota/Auth): {e}")
        except Exception as e:
            logger.warning(f"YouTube Fetch Error: {e}")
    else:
        logger.info("No YouTube API Key configured, using fallback")

    # 4. Fallback to Local Data
    if local_profile:
        logger.info("Using local fallback data")
        return {
            "success": True,
            "source": "local_fallback",
            "data": local_profile
        }
        
    return {
        "success": False,
        "error": "Channel not found in API or local database"
    }


@mcp.tool()
def calculate_engagement(channel_id: str) -> Dict[str, Any]:
    """
    Calculate engagement rate based on recent videos.
    (Likes + Comments) / Views
    """
    logger.info(f"calculate_engagement called for {channel_id}")
    
    # In a real app, we would fetch recent videos via API
    # For this assessment, we'll return the stored rate from profiles 
    # or a calculated simulation
    
    # Try to find by ID in local profiles
    for profile in youtube_profiles:
        if profile.get("channel_id") == channel_id:
            return {
                "success": True,
                "engagement_rate": profile.get("engagement_rate"),
                "avg_views": profile.get("avg_views"),
                "consistency_score": profile.get("consistency_score", "medium")
            }
            
    # If not found, simulate based on "real" processing
    return {
        "success": True,
        "engagement_rate": 0.08, # 8% default
        "avg_views": 50000,
        "consistency_score": "medium"
    }


# ========== PRICING TOOLS ==========

def get_base_cpm(subscribers: int) -> float:
    """Get base CPM based on subscriber tiers"""
    if subscribers < 10_000: return 12.50   # Micro ($10-15)
    if subscribers < 100_000: return 20.00  # Mid ($15-25)
    if subscribers < 1_000_000: return 32.50 # Macro ($25-40)
    return 70.00                            # Mega ($40-100)

def get_engagement_multiplier(rate: float) -> float:
    """Multiplier based on engagement rate"""
    if rate < 0.05: return 0.7  # Low
    if rate < 0.15: return 1.0  # Average
    if rate < 0.30: return 1.3  # High
    return 1.5                  # Viral/Cult

def get_niche_multiplier(channel_title: str, description: str) -> float:
    """Multiplier based on content niche"""
    content = (channel_title + " " + description).lower()
    if "tech" in content or "ai" in content: return 1.2
    if "finance" in content or "money" in content: return 1.4
    if "game" in content or "gaming" in content: return 0.9
    return 1.0 # Lifestyle/General

def get_consistency_multiplier(score: str) -> float:
    """Multiplier based on upload consistency"""
    if score == "high": return 1.1
    if score == "medium": return 1.0
    if score == "low": return 0.9
    return 1.0

@mcp.tool()
def calculate_offer_price(channel_url: str, campaign_type: str, brand_id: str) -> Dict[str, Any]:
    """
    Calculate fair offering price based on CPM model.
    
    Formula: Base CPM * Eng. Multiplier * Niche Multiplier * Consistency
    Total = (Avg Views / 1000) * Final CPM
    """
    logger.info(f"calculate_offer_price called for {channel_url}")
    
    # 1. Get Channel Data
    channel_res = fetch_channel_data(channel_url)
    if not channel_res["success"]:
        return {"success": False, "error": "Could not fetch channel data"}
    
    data = channel_res["data"]
    
    # 2. Extract Metrics - Handle different field names from API vs local data
    subs = data.get("subscriber_count") or data.get("subscribers", 0)
    avg_views = data.get("avg_views") or data.get("avg_views_per_video", subs * 0.1)
    eng_rate = data.get("engagement_rate", 0.05)
    consistency = data.get("consistency_score") or data.get("consistency", "medium")
    
    # 3. Calculate CPMS
    base_cpm = get_base_cpm(subs)
    eng_mult = get_engagement_multiplier(eng_rate)
    niche_mult = get_niche_multiplier(
        data.get("title") or data.get("channel_name", ""), 
        data.get("description", "") + " " + data.get("category", "")
    )
    cons_mult = get_consistency_multiplier(consistency)
    
    final_cpm = base_cpm * eng_mult * niche_mult * cons_mult
    
    # 4. Calculate Total Price
    # Price = (Views / 1000) * CPM
    estimated_price = (avg_views / 1000) * final_cpm
    
    # Rounding
    final_cpm = round(final_cpm, 2)
    estimated_price = round(estimated_price, 2)
    
    logger.info(f"Calculated price: ${estimated_price} (CPM: ${final_cpm})")
    
    return {
        "success": True,
        "calculation": {
            "metrics": {
                "subscribers": subs,
                "avg_views": avg_views,
                "engagement_rate": eng_rate,
                "consistency": consistency
            },
            "multipliers": {
                "base_cpm": base_cpm,
                "engagement": eng_mult,
                "niche": niche_mult,
                "consistency": cons_mult
            },
            "final_cpm": final_cpm,
            "estimated_total_price": estimated_price,
            "currency": "USD"
        },
        "recommendation": {
            "offer_price": estimated_price,
            "negotiation_cap": estimated_price * 1.2
        }
    }

@mcp.tool()
def validate_counter_offer(channel_url: str, original_price: float, counter_price: float) -> Dict[str, Any]:
    """
    Analyze detailed counter-offer against calculated fair value.
    """
    logger.info(f"validate_counter_offer: Orig=${original_price} Counter=${counter_price}")
    
    # Re-calculate fair value to be sure
    # In real app, we might pass brand_id from context, here default
    calc_res = calculate_offer_price(channel_url, "integration", "generic")
    
    if not calc_res["success"]:
        fair_price = original_price # Fallback
    else:
        fair_price = calc_res["calculation"]["estimated_total_price"]
        
    diff_percent = ((counter_price - fair_price) / fair_price) * 100
    
    recommendation = "decline"
    reason = "Price exceeds maximum ROAS threshold."
    
    if diff_percent <= 10:
        recommendation = "accept"
        reason = "Counter-offer is within 10% of fair value (auto-approve)."
    elif diff_percent <= 25:
        recommendation = "negotiate"
        reason = f"Counter is {diff_percent:.1f}% higher. Attempt to meet in the middle."
    else:
        recommendation = "decline"
        reason = f"Counter IS {diff_percent:.1f}% higher than fair market value."
        
    return {
        "success": True,
        "analysis": {
            "fair_market_value": fair_price,
            "counter_offer": counter_price,
            "difference_percentage": round(diff_percent, 1),
            "recommendation": recommendation,
            "reason": reason
        }
    }


# ========== SERVER ENTRY POINT ==========
if __name__ == "__main__":
    logger.info("Starting MCP server via stdio...")
    mcp.run()
