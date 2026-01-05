"""
Test YouTube Data API v3 Integration

This script tests the fetch_channel_data tool with real YouTube channels
to verify the API is working correctly and fallback logic is sound.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys

# Test channels with different characteristics
TEST_CHANNELS = [
    {
        "name": "Fireship (Tech)",
        "url": "https://www.youtube.com/@Fireship",
        "expected_subs": 3_500_000,  # ~3.5M subs (as of 2024)
        "category": "tech"
    },
    {
        "name": "Veritasium (Science)",
        "url": "https://www.youtube.com/@veritasium",
        "expected_subs": 16_000_000,  # ~16M subs
        "category": "science"
    },
    {
        "name": "MKBHD (Tech Reviews)",
        "url": "https://www.youtube.com/@mkbhd",
        "expected_subs": 19_000_000,  # ~19M subs
        "category": "tech"
    },
    {
        "name": "Local Fallback Test",
        "url": "https://www.youtube.com/@TechReviewAlex",
        "expected_subs": 100_000,  # Should fallback to local data
        "category": "tech"
    },
]


async def test_youtube_api():
    """Test YouTube API integration via MCP"""

    print("=" * 70)
    print("YouTube Data API v3 Integration Test")
    print("=" * 70)
    print()

    # Spawn MCP server
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ MCP server initialized\n")

            results = []

            for channel in TEST_CHANNELS:
                print(f"Testing: {channel['name']}")
                print(f"URL: {channel['url']}")
                print("-" * 70)

                try:
                    # Call MCP tool
                    result = await session.call_tool(
                        "fetch_channel_data",
                        {"channel_url": channel["url"]}
                    )

                    # Parse result
                    if hasattr(result, 'content') and len(result.content) > 0:
                        content_text = result.content[0].text
                        data = json.loads(content_text)

                        if data.get("success"):
                            channel_data = data.get("data", {})
                            source = data.get("source", "unknown")

                            subs = channel_data.get("subscriber_count") or channel_data.get("subscribers", 0)
                            title = channel_data.get("title") or channel_data.get("channel_name", "Unknown")
                            engagement = channel_data.get("engagement_rate", 0)

                            # Determine if real API or fallback
                            if source == "api":
                                status = "✅ REAL API"
                                color = "\033[92m"  # Green
                            elif source == "local_fallback":
                                status = "⚠️  FALLBACK"
                                color = "\033[93m"  # Yellow
                            else:
                                status = "❓ UNKNOWN"
                                color = "\033[94m"  # Blue

                            reset = "\033[0m"

                            print(f"{color}Source: {status}{reset}")
                            print(f"Channel: {title}")
                            print(f"Subscribers: {subs:,}")
                            print(f"Engagement Rate: {engagement*100:.2f}%")

                            results.append({
                                "channel": channel["name"],
                                "source": source,
                                "subscribers": subs,
                                "success": True
                            })
                        else:
                            print(f"❌ ERROR: {data.get('error')}")
                            results.append({
                                "channel": channel["name"],
                                "source": "error",
                                "success": False,
                                "error": data.get("error")
                            })
                    else:
                        print("❌ ERROR: Invalid response format")
                        results.append({
                            "channel": channel["name"],
                            "source": "error",
                            "success": False,
                            "error": "Invalid response"
                        })

                except Exception as e:
                    print(f"❌ EXCEPTION: {str(e)}")
                    results.append({
                        "channel": channel["name"],
                        "source": "exception",
                        "success": False,
                        "error": str(e)
                    })

                print()

            # Summary
            print("=" * 70)
            print("TEST SUMMARY")
            print("=" * 70)

            api_count = sum(1 for r in results if r.get("source") == "api")
            fallback_count = sum(1 for r in results if r.get("source") == "local_fallback")
            error_count = sum(1 for r in results if not r.get("success"))

            print(f"Total Tests: {len(results)}")
            print(f"✅ Real API: {api_count}")
            print(f"⚠️  Fallback: {fallback_count}")
            print(f"❌ Errors: {error_count}")
            print()

            if api_count > 0:
                print("🎉 SUCCESS! YouTube Data API v3 is working!")
            elif fallback_count == len(results):
                print("⚠️  WARNING: All requests used fallback. Check your API key.")
                print("   - Verify YOUTUBE_API_KEY in .env")
                print("   - Check if API is enabled in Google Cloud Console")
                print("   - Ensure you restarted the backend after updating .env")
            else:
                print("❌ MIXED RESULTS: Some API calls failed")

            print()


if __name__ == "__main__":
    asyncio.run(test_youtube_api())
